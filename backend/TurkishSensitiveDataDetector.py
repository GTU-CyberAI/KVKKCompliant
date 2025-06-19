from io import BytesIO
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import re
import spacy
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
import json
import fitz 
from fpdf import FPDF

app = Flask(__name__)
CORS(app)


FONT_URL = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
FONT_PATH = "NotoSans-Regular.ttf"

# Font dosyası yoksa indir
def ensure_font_exists():
    if not os.path.exists(FONT_PATH):
        print("⏬ Font indiriliyor...")
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
        print("✅ Font indirildi.")
class TurkishSensitiveDataDetector:
    def __init__(self):
        self.anonymizer = AnonymizerEngine()
        
        # Türkçe NLP motoru
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "tr", "model_name": "tr_core_news_trf"}]
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()
        
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["tr"])

        # Ayrıca bu da NLP ile kullanılacak:
        self.nlp = spacy.load("tr_core_news_trf")

        # Regex desenleri - geliştirilmiş
        self.patterns = {
            'tc_kimlik': r'\b[1-9][0-9]{10}\b',
            'phone': r'\b(\+90|0)?5\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'iban': r'TR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}',
            'credit_card': r'\b(?:\d{4}[\s\-]?){3}\d{4}\b',
            'birthday': r'\b(?:\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})\b',
            # Yeni desenler
            'address_component': r'\b(?:Mahalle|Mah\.|Sokak|Sok\.|Cadde|Cad\.|Bulvar|Blv\.|No:|Daire:|Kat:)\b',
            'medical_condition': r'\b(?:depresyon|anksiyete|panik atak|bipolar|şizofreni|ocd|ptsd|adhd|otizm|epilepsi|migren|astım|diyabet|hipertansiyon|kalp krizi|felç|kanser|tümör|hepatit|hiv|aids)\b',
            'medication': r'\b(?:prozac|xanax|zoloft|lexapro|wellbutrin|abilify|risperdal|lithium|ritalin|adderall|insulin|metformin|aspirin|parol|nurofen|voltaren|majezik|minoset|cipralex|sertralin|venlafaksin)\b'
        }
        
        # Türkiye'deki yaygın mahalle, sokak isimleri (genişletilebilir)
        self.location_keywords = {
            'mahalle': ['Bahçelievler', 'Kızılay', 'Çankaya', 'Beşiktaş', 'Kadıköy', 'Üsküdar', 'Fatih', 'Beyoğlu', 
                       'Şişli', 'Bakırköy', 'Zeytinburnu', 'Maltepe', 'Pendik', 'Kartal', 'Ataşehir', 'Levent',
                       'Etiler', 'Nişantaşı', 'Ortaköy', 'Bostancı', 'Fenerbahçe', 'Göztepe', 'Acıbadem'],
            'sokak': ['Güneş', 'Barış', 'Hürriyet', 'Cumhuriyet', 'Atatürk', 'İnönü', 'Menderes', 'Özgürlük',
                     'Kurtuluş', 'Zafer', 'Vatan', 'Millet', 'Türk', 'Anadolu', 'İstiklal', 'Gazi', 'Şehit'],
            'city': ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Adana', 'Konya', 'Gaziantep', 'Kayseri', 'Mersin']
        }

    def validate_tc_kimlik(self, tc_no):
        """Validate Turkish ID number using checksum algorithm"""
        if len(tc_no) != 11 or not tc_no.isdigit():
            return False
        
        digits = [int(d) for d in tc_no]
        
        # First 9 digits checksum
        odd_sum = sum(digits[i] for i in range(0, 9, 2))
        even_sum = sum(digits[i] for i in range(1, 9, 2))
        
        if (odd_sum * 7 - even_sum) % 10 != digits[9]:
            return False
        
        # All digits checksum
        if sum(digits[:10]) % 10 != digits[10]:
            return False
        
        return True
    
    def validate_luhn(self, card_number):
        """Validate credit card using Luhn algorithm"""
        card_number = re.sub(r'\D', '', card_number)
        if len(card_number) < 13 or len(card_number) > 19:
            return False
        
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        return luhn_checksum(card_number) == 0
    
    def detect_location_components(self, text):
        """Detect Turkish address components and location names"""
        detections = []
        
        # Genel adres bileşenleri (Mah., Sok., vb.)
        for match in re.finditer(self.patterns['address_component'], text, re.IGNORECASE):
            detections.append({
                'entity_type': 'ADDRESS_COMPONENT',
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'confidence': 0.7
            })
        
        # Bilinen mahalle, sokak isimleri
        for category, locations in self.location_keywords.items():
            for location in locations:
                pattern = r'\b' + re.escape(location) + r'\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    detections.append({
                        'entity_type': 'LOCATION_NAME',
                        'start': match.start(),
                        'end': match.end(),
                        'text': match.group(),
                        'confidence': 0.85
                    })
        
        return detections
    
    def detect_medical_information(self, text):
        """Detect medical conditions and medications"""
        detections = []
        
        # Tıbbi durumlar
        for match in re.finditer(self.patterns['medical_condition'], text, re.IGNORECASE):
            detections.append({
                'entity_type': 'MEDICAL_CONDITION',
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'confidence': 0.9
            })
        
        # İlaçlar
        for match in re.finditer(self.patterns['medication'], text, re.IGNORECASE):
            detections.append({
                'entity_type': 'MEDICATION',
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'confidence': 0.9
            })
        
        return detections
    
    def detect_regex_patterns(self, text):
        """Detect sensitive data using regex patterns"""
        detections = []
        print(text)
        # 1. TC Kimlik No detection
        tc_matches = re.finditer(self.patterns['tc_kimlik'], text)
        for match in tc_matches:
            tc_no = match.group()
            print("lollllllllllllll")
            print(tc_no)
            if self.validate_tc_kimlik(tc_no):
                detections.append({
                    'entity_type': 'TC_KIMLIK',
                    'start': match.start(),
                    'end': match.end(),
                    'text': tc_no,
                    'confidence': 0.95
                })

        # 2. Credit card detection
        cc_matches = re.finditer(self.patterns['credit_card'], text)
        for match in cc_matches:
            cc_number = match.group()
            if self.validate_luhn(cc_number):
                detections.append({
                    'entity_type': 'CREDIT_CARD',
                    'start': match.start(),
                    'end': match.end(),
                    'text': cc_number,
                    'confidence': 0.95
                })

        # 3. Email detection
        email_matches = re.finditer(self.patterns['email'], text)
        for match in email_matches:
            detections.append({
                'entity_type': 'EMAIL',
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'confidence': 0.95
            })

        # 4. IBAN detection
        iban_matches = re.finditer(self.patterns['iban'], text, re.IGNORECASE)
        for match in iban_matches:
            detections.append({
                'entity_type': 'IBAN',
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'confidence': 0.9
            })

        # 5. Phone number detection (en sonda)
        phone_matches = re.finditer(self.patterns['phone'], text)
        for match in phone_matches:
            detections.append({
                'entity_type': 'PHONE_NUMBER',
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'confidence': 0.9
            })
        # Doğum tarihi
        birthday_matches = re.finditer(self.patterns['birthday'], text)
        for match in birthday_matches:
            detections.append({
                'entity_type': 'BIRTHDAY',
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'confidence': 0.9
            })


        return detections

    
    def detect_nlp_entities(self, text):
        """Detect entities using spaCy NLP"""
        doc = self.nlp(text)
        detections = []
        
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'PER', 'KIŞI']:
                detections.append({
                    'entity_type': 'PERSON',
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'text': ent.text,
                    'confidence': 0.8
                })
            elif ent.label_ in ['GPE', 'LOC', 'YER']:
                detections.append({
                    'entity_type': 'LOCATION',
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'text': ent.text,
                    'confidence': 0.7
                })
        
        return detections
    
    def mask_text(self, text, detections):
        """Apply masking to detected sensitive data - geliştirilmiş"""
        # Sort detections by start position (reverse order for replacement)
        sorted_detections = sorted(detections, key=lambda x: x['start'], reverse=True)
        
        masked_text = text
        
        for detection in sorted_detections:
            start = detection['start']
            end = detection['end']
            entity_type = detection['entity_type']
            original_text = detection['text']
            
            # Apply different masking strategies
            if entity_type == 'TC_KIMLIK':
                masked = original_text[:2] + '*' * 7 + original_text[-2:]
            
            elif entity_type == 'PHONE_NUMBER':
                digits = re.sub(r'\D', '', original_text)
                masked_digits = digits[:3] + '*'*(len(digits)-5) + digits[-2:]
                # Orijinal formatı koru
                idx = 0
                masked = ''
                for ch in original_text:
                    if ch.isdigit():
                        masked += masked_digits[idx]
                        idx += 1
                    else:
                        masked += ch
                        
            elif entity_type == 'BIRTHDAY':
                masked = '[DOĞUM TARİHİ]'
                
            elif entity_type == 'EMAIL':
                if '@' in original_text:
                    local, domain = original_text.split('@', 1)
                    masked_local = local[0] + '*' * (len(local) - 1) if len(local) > 1 else '*'
                    masked = masked_local + '@' + domain
                else:
                    masked = '*' * len(original_text)
            
            elif entity_type == 'CREDIT_CARD':
                # DÜZELTME: Tüm kart numarası maskelenmeli, sadece son 4 hane görünür
                cleaned = re.sub(r'\D', '', original_text)
                if len(cleaned) > 4:
                    # Son 4 haneyi koru, geri kalanını maskele
                    masked_cleaned = '*' * (len(cleaned) - 4) + cleaned[-4:]
                    
                    # Orijinal formatı koru (boşluk, tire vb.)
                    masked = ''
                    clean_idx = 0
                    for char in original_text:
                        if char.isdigit():
                            masked += masked_cleaned[clean_idx]
                            clean_idx += 1
                        else:
                            masked += char
                else:
                    masked = '*' * len(original_text)
            
            elif entity_type == 'IBAN':
                masked = original_text[:4] + '*' * (len(original_text) - 8) + original_text[-4:]
            
            elif entity_type == 'PERSON':
                # İsim maskeleme
                parts = original_text.split()
                if len(parts) > 1:
                    masked_parts = []
                    for part in parts:
                        if len(part) > 2:
                            masked_parts.append(part[0] + '*' * (len(part) - 2) + part[-1])
                        else:
                            masked_parts.append('*' * len(part))
                    masked = ' '.join(masked_parts)
                else:
                    if len(original_text) > 2:
                        masked = original_text[0] + '*' * (len(original_text) - 2) + original_text[-1]
                    else:
                        masked = '*' * len(original_text)
            
            elif entity_type in ['LOCATION_NAME', 'ADDRESS_COMPONENT']:
                # Lokasyon maskeleme
                if len(original_text) > 3:
                    masked = original_text[:2] + '*' * (len(original_text) - 2)
                else:
                    masked = '*' * len(original_text)
            
            elif entity_type in ['MEDICAL_CONDITION', 'MEDICATION']:
                # Tıbbi bilgi maskeleme
                masked = '[TIBBİ BİLGİ]'
            
            else:
                masked = '*' * len(original_text)
            
            masked_text = masked_text[:start] + masked + masked_text[end:]
        
        return masked_text
    
    def analyze_and_mask(self, text):
        self.text = text
        """Main method to detect and mask sensitive data"""
        # Tüm tespit yöntemlerini birleştir
        regex_detections = self.detect_regex_patterns(text)
        nlp_detections = self.detect_nlp_entities(text)
        location_detections = self.detect_location_components(text)
        medical_detections = self.detect_medical_information(text)
        
        # Yakın sayıları birleştir
        merged_regex = self.merge_adjacent_numbers(regex_detections)
        
        all_detections = (merged_regex + nlp_detections + 
                         location_detections + medical_detections)
        
        # Çakışan tespitleri temizle
        filtered_detections = self.remove_overlaps(all_detections)
        
        # Maskeleme uygula
        masked_text = self.mask_text(text, filtered_detections)
        
        return {
            'original_text': text,
            'masked_text': masked_text,
            'detections': filtered_detections,
            'detection_count': len(filtered_detections),
            'detection_types': {
                'regex': len(merged_regex),
                'nlp': len(nlp_detections),
                'location': len(location_detections),
                'medical': len(medical_detections)
            }
        }
    
    def merge_adjacent_numbers(self, detections):
        """Yakın rakamları birleştir"""
        if not detections:
            return []
            
        merged = []
        detections.sort(key=lambda x: x['start'])
        
        for det in detections:
            if merged and det['entity_type'] == merged[-1]['entity_type']:
                prev = merged[-1]
                # Arada yalnızca boşluk-tire gibi ayraç varsa → birleştir
                gap = det['start'] - prev['end']
                if gap <= 2 and re.fullmatch(r'[\s\-]*', self.text[prev['end']:det['start']]):
                    prev['end'] = det['end']
                    prev['text'] = self.text[prev['start']:det['end']]
                    continue
            merged.append(det)
        return merged

    def remove_overlaps(self, detections):
        """Remove overlapping detections, keeping higher confidence ones"""
        if not detections:
            return []
        
        # Start pozisyonuna göre sırala
        sorted_detections = sorted(detections, key=lambda x: x['start'])
        filtered = []
        
        for current in sorted_detections:
            # Çakışma kontrolü
            overlapping = False
            for i, existing in enumerate(filtered):
                # Çakışma var mı?
                if not (current['end'] <= existing['start'] or current['start'] >= existing['end']):
                    overlapping = True
                    # Daha yüksek confidence'ı tut
                    if current['confidence'] > existing['confidence']:
                        filtered[i] = current
                    break
            
            if not overlapping:
                filtered.append(current)
        
        return filtered

# Initialize detector
detector = TurkishSensitiveDataDetector()

@app.route('/api/mask', methods=['POST'])
def mask_text():
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        
        if not text.strip():
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        result = detector.analyze_and_mask(text)
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """Endpoint for debugging - returns only detections without masking"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        detector.text = text
        
        regex_detections = detector.detect_regex_patterns(text)
        nlp_detections = detector.detect_nlp_entities(text)
        location_detections = detector.detect_location_components(text)
        medical_detections = detector.detect_medical_information(text)
        
        return jsonify({
            'success': True,
            'data': {
                'regex_detections': regex_detections,
                'nlp_detections': nlp_detections,
                'location_detections': location_detections,
                'medical_detections': medical_detections,
                'total_detections': (len(regex_detections) + len(nlp_detections) + 
                                   len(location_detections) + len(medical_detections))
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Enhanced KVKK Compliant Data Masking API',
        'features': [
            'Turkish ID validation',
            'Credit card masking (Luhn validated)',
            'Turkish address component detection',
            'Medical information masking',
            'Enhanced location detection',
            'NLP-based entity recognition'
        ]
    })

@app.route('/api/mask_pdf', methods=['POST'])
def mask_pdf():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400
    
    file = request.files.get('file')
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Only PDF files are supported'}), 400

    try:
        # PDF'i oku
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"

        result = detector.analyze_and_mask(full_text)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    



@app.route('/api/export_pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.get_json()
        masked_text = data.get("masked_text", "")
        if not masked_text:
            return jsonify({"error": "Eksik metin"}), 400

        ensure_font_exists()

        pdf = FPDF()
        pdf.add_page()
        pdf.add_font("NotoSans", "", FONT_PATH, uni=True)
        pdf.set_font("NotoSans", size=12)
        pdf.multi_cell(0, 10, masked_text)

        # PDF'yi hafızaya yaz
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        return send_file(
            pdf_output,
            mimetype='application/pdf',
            download_name='maskelenmis_metin.pdf',
            as_attachment=True
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Enhanced KVKK Compliant Data Masking System...")
    print("Available endpoints:")
    print("- POST /api/mask - Detect and mask sensitive data")
    print("- POST /api/analyze - Analyze text for sensitive data (debug)")
    print("- GET /api/health - Health check")
    print("\nNew features:")
    print("✓ Fixed credit card masking (only last 4 digits visible)")
    print("✓ Turkish address component detection")
    print("✓ Medical condition and medication detection")
    print("✓ Enhanced location name recognition")
    print("✓ Improved overlap detection")
    
    app.run(debug=True, host='0.0.0.0', port=5000)