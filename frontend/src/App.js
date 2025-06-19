import React, { useState } from 'react';
import { AlertCircle, Shield, Eye, EyeOff, Copy, Download, Upload } from 'lucide-react';

const SensitiveDataMaskingApp = () => {
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);
  const [activeTab, setActiveTab] = useState('text');

  const handleAnalyze = async () => {
    if (!inputText.trim()) {
      alert('Lütfen analiz edilecek metni girin.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/mask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: inputText }),
      });

      const data = await response.json();
      
      if (data.success) {
        setResult(data.data);
      } else {
        alert('Hata: ' + data.error);
      }
    } catch (error) {
      alert('Bağlantı hatası: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();

  if (file.type === 'text/plain') {
    reader.onload = (e) => {
      setInputText(e.target.result);
      setActiveTab('text');
    };
    reader.readAsText(file);
  } else if (file.type === 'application/pdf') {
  const formData = new FormData();
  formData.append('file', file);

  setLoading(true);
  fetch('http://localhost:5000/api/mask_pdf', {
    method: 'POST',
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        setResult(data.data);
        setInputText(data.data.original_text || '');
        setActiveTab('text');
      } else {
        alert('Hata: ' + data.error);
      }
    })
    .catch((err) => alert('PDF bağlantı hatası: ' + err.message))
    .finally(() => setLoading(false));
}

   else {
    alert('Lütfen sadece .txt veya .pdf dosyası yükleyin.');
  }
};


const exportToPDF = async () => {
  if (!result) return;

  const res = await fetch('http://localhost:5000/api/export_pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ masked_text: result.masked_text })
  });

  if (!res.ok) {
    alert("PDF export hatası");
    return;
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'maskelenmis_metin.pdf';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Metin panoya kopyalandı!');
  };

const downloadResult = () => {
  if (!result) return;

  if (result.masked_pdf_base64) {
    const link = document.createElement('a');
    link.href = `data:application/pdf;base64,${result.masked_pdf_base64}`;
    link.download = 'maskelenmis_metin.pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } else {
    const file = new Blob([result.masked_text], { type: 'text/plain' });
    const element = document.createElement('a');
    element.href = URL.createObjectURL(file);
    element.download = 'maskelenmiş_metin.txt';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }
};

  const getEntityTypeColor = (type) => {
    const colors = {
      'TC_KIMLIK': 'bg-red-100 text-red-800',
      'PHONE_NUMBER': 'bg-blue-100 text-blue-800',
      'EMAIL': 'bg-green-100 text-green-800',
      'CREDIT_CARD': 'bg-purple-100 text-purple-800',
      'IBAN': 'bg-yellow-100 text-yellow-800',
      'PERSON': 'bg-indigo-100 text-indigo-800',
      'LOCATION': 'bg-pink-100 text-pink-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  
  const getEntityTypeName = (type) => {
    const names = {
      'TC_KIMLIK': 'TC Kimlik No',
      'PHONE_NUMBER': 'Telefon Numarası',
      'EMAIL': 'E-posta',
      'CREDIT_CARD': 'Kredi Kartı',
      'IBAN': 'IBAN',
      'PERSON': 'Kişi Adı',
      'LOCATION': 'Konum',
    };
    return names[type] || type;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Shield className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-800">
              Hassas Veri Tespit ve Maskeleme Sistemi
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            KVKK uyumlu olarak Türkçe metinlerdeki hassas kişisel verileri otomatik tespit eder ve maskeler.
            TC Kimlik numaraları, telefon numaraları, e-posta adresleri ve daha fazlasını güvenli hale getirir.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
              <Upload className="h-6 w-6 mr-2" />
              Metin Girişi
            </h2>

            {/* Tab Navigation */}
            <div className="flex mb-4 border-b">
              <button
                className={`px-4 py-2 font-medium ${
                  activeTab === 'text'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
                onClick={() => setActiveTab('text')}
              >
                Metin Girişi
              </button>
              <button
                className={`px-4 py-2 font-medium ${
                  activeTab === 'file'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
                onClick={() => setActiveTab('file')}
              >
                Dosya Yükleme
              </button>
            </div>

            {activeTab === 'text' ? (
              <textarea
                className="w-full h-64 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Analiz edilecek metni buraya yazın veya yapıştırın...&#10;&#10;Örnek: &#10;Adım Ahmet Yılmaz, TC Kimlik Numaram 12345678901.&#10;Telefon numaram 0532 123 45 67.&#10;E-posta adresim ahmet@example.com"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
              />
            ) : (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <label className="cursor-pointer">
                  <span className="text-lg text-gray-600">
                    Dosya seçmek için tıklayın
                  </span>
                  <input
                    type="file"
                    className="hidden"
                    accept=".txt,application/pdf"
                    onChange={handleFileUpload}
                  />
                </label>
                <p className="text-sm text-gray-500 mt-2">
                  Sadece .txt ve .pdf dosyaları desteklenmektedir
                </p>
              </div>
            )}

            <div className="mt-6 flex justify-between items-center">
              <div className="text-sm text-gray-500">
                Karakter sayısı: {inputText.length}
              </div>
              <button
                onClick={handleAnalyze}
                disabled={loading || !inputText.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Analiz Ediliyor...
                  </>
                ) : (
                  <>
                    <Shield className="h-4 w-4 mr-2" />
                    Analiz Et ve Maskele
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
              <Eye className="h-6 w-6 mr-2" />
              Analiz Sonuçları
            </h2>

            {!result ? (
              <div className="flex items-center justify-center h-64 text-gray-500">
                <div className="text-center">
                  <Shield className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <p>Metin analiz sonuçları burada görünecek</p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Statistics */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-800">Tespit Edilen Hassas Veri</h3>
                      <p className="text-2xl font-bold text-blue-600">{result.detection_count}</p>
                    </div>
                    <AlertCircle className="h-12 w-12 text-blue-500" />
                  </div>
                </div>

                {/* Detection Details */}
                {result.detections && result.detections.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-3">Tespit Edilen Veriler:</h3>
                    <div className="space-y-2">
                      {result.detections.map((detection, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div className="flex items-center">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getEntityTypeColor(detection.entity_type)}`}>
                              {getEntityTypeName(detection.entity_type)}
                            </span>
                            <span className="ml-3 text-gray-600 font-mono">
                              {detection.text}
                            </span>
                          </div>
                          <span className="text-sm text-gray-500">
                            %{Math.round(detection.confidence * 100)} güven
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Masked Text */}
            <div>
  <div className="flex items-center justify-between mb-3">
    <h3 className="font-semibold text-gray-800">Maskelenmiş Metin:</h3>
    <div className="flex space-x-2">
      <button
        onClick={() => setShowOriginal(!showOriginal)}
        className="flex items-center text-sm text-blue-600 hover:text-blue-800"
      >
        {showOriginal ? <EyeOff className="h-4 w-4 mr-1" /> : <Eye className="h-4 w-4 mr-1" />}
        {showOriginal ? 'Orijinali Gizle' : 'Orijinali Göster'}
      </button>

      <button
        onClick={() => copyToClipboard(result.masked_text)}
        className="flex items-center text-sm text-gray-600 hover:text-gray-800"
      >
        <Copy className="h-4 w-4 mr-1" />
        Kopyala
      </button>

      <button
        onClick={downloadResult}
        className="flex items-center text-sm text-gray-600 hover:text-gray-800"
      >
        <Download className="h-4 w-4 mr-1" />
        TXT İndir
      </button>

      <button
        onClick={exportToPDF}
        className="flex items-center text-sm text-gray-600 hover:text-gray-800"
      >
        <Download className="h-4 w-4 mr-1" />
        PDF İndir
      </button>
    </div>
  </div>

  <div className="space-y-4">
    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
      <div className="text-sm text-green-600 font-medium mb-2">✓ Maskelenmiş (Güvenli)</div>
      <div className="font-mono text-sm text-gray-800 whitespace-pre-wrap">
        {result.masked_text}
      </div>
    </div>

    {showOriginal && (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="text-sm text-red-600 font-medium mb-2">⚠ Orijinal (Hassas Veri İçerir)</div>
        <div className="font-mono text-sm text-gray-800 whitespace-pre-wrap">
          {result.original_text}
        </div>
      </div>
    )}
  </div>
</div>

              </div>
            )}
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Sistem Özellikleri</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <Shield className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <h4 className="font-medium text-gray-800">KVKK Uyumlu</h4>
              <p className="text-sm text-gray-600">Türk veri koruma yasalarına uygun</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <Eye className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <h4 className="font-medium text-gray-800">Otomatik Tespit</h4>
              <p className="text-sm text-gray-600">AI destekli hassas veri tanıma</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <AlertCircle className="h-8 w-8 text-purple-600 mx-auto mb-2" />
              <h4 className="font-medium text-gray-800">Çoklu Format</h4>
              <p className="text-sm text-gray-600">TC Kimlik, telefon, e-posta destekli</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <Download className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
              <h4 className="font-medium text-gray-800">Kolay Kullanım</h4>
              <p className="text-sm text-gray-600">Basit arayüz ve hızlı işlem</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SensitiveDataMaskingApp;