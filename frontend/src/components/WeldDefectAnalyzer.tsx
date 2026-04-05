/**
 * Weld Defect Analyzer - Visual Diagnosis with Image Upload
 * Uses Claude Vision API for real-time weld defect analysis
 */

import React, { useState, useRef } from 'react';
import { Upload, Camera, AlertCircle, Loader2, CheckCircle, X } from 'lucide-react';
import axios from 'axios';

interface DefectAnalysis {
  defects: string[];
  severity: 'low' | 'medium' | 'high';
  causes: string[];
  solutions: string[];
  settingsRecommendation?: {
    voltage?: string;
    amperage?: string;
    wireSpeed?: string;
    technique?: string;
  };
}

interface WeldDefectAnalyzerProps {
  apiUrl: string;
}

const WeldDefectAnalyzer: React.FC<WeldDefectAnalyzerProps> = ({ apiUrl }) => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<DefectAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setSelectedImage(e.target?.result as string);
      setError(null);
      setAnalysis(null);
    };
    reader.readAsDataURL(file);
  };

  const analyzeWeld = async () => {
    if (!selectedImage) return;

    setLoading(true);
    setError(null);

    try {
      // Extract base64 data
      const base64Data = selectedImage.split(',')[1];

      const response = await axios.post(`${apiUrl}/analyze-weld`, {
        image: base64Data
      });

      setAnalysis(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze weld. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const reset = () => {
    setSelectedImage(null);
    setAnalysis(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-500 to-orange-500 px-6 py-4">
        <div className="flex items-center space-x-3">
          <Camera className="w-6 h-6 text-white" />
          <div>
            <h2 className="text-xl font-bold text-white">Weld Defect Analyzer</h2>
            <p className="text-sm text-white/90">Upload a photo of your weld for instant AI diagnosis</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Upload Area */}
        {!selectedImage ? (
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-orange-400 transition-colors">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
              id="weld-upload"
            />
            <label
              htmlFor="weld-upload"
              className="cursor-pointer flex flex-col items-center space-y-4"
            >
              <div className="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center">
                <Upload className="w-10 h-10 text-orange-500" />
              </div>
              <div>
                <p className="text-lg font-medium text-gray-900 mb-1">
                  Upload Weld Photo
                </p>
                <p className="text-sm text-gray-500">
                  Click to browse or drag and drop
                </p>
              </div>
              <div className="text-xs text-gray-400">
                Supports: JPG, PNG, WEBP
              </div>
            </label>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Image Preview */}
            <div className="relative">
              <img
                src={selectedImage}
                alt="Weld to analyze"
                className="w-full h-auto rounded-lg shadow-md max-h-96 object-contain bg-gray-100"
              />
              <button
                onClick={reset}
                className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 text-white rounded-full p-2 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Analyze Button */}
            {!analysis && !loading && (
              <button
                onClick={analyzeWeld}
                disabled={loading}
                className="w-full px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-medium rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                <Camera className="w-5 h-5" />
                <span>Analyze Weld Quality</span>
              </button>
            )}

            {/* Loading State */}
            {loading && (
              <div className="flex items-center justify-center space-x-3 py-8">
                <Loader2 className="w-6 h-6 animate-spin text-orange-500" />
                <span className="text-gray-600">Analyzing weld defects...</span>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-800">Analysis Failed</p>
                  <p className="text-sm text-red-600 mt-1">{error}</p>
                </div>
              </div>
            )}

            {/* Analysis Results */}
            {analysis && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Severity Badge */}
                <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full border ${getSeverityColor(analysis.severity)}`}>
                  {analysis.severity === 'low' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                  <span className="font-semibold text-sm uppercase">
                    {analysis.severity} Severity
                  </span>
                </div>

                {/* Detected Defects */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2 flex items-center space-x-2">
                    <AlertCircle className="w-5 h-5 text-orange-500" />
                    <span>Detected Issues</span>
                  </h3>
                  <ul className="space-y-1">
                    {analysis.defects.map((defect, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <span className="text-orange-500 mr-2">•</span>
                        <span>{defect}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Causes */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Possible Causes</h3>
                  <ul className="space-y-1">
                    {analysis.causes.map((cause, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        <span>{cause}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Solutions */}
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Recommended Solutions</h3>
                  <ol className="space-y-2">
                    {analysis.solutions.map((solution, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <span className="text-green-600 font-semibold mr-2">{idx + 1}.</span>
                        <span>{solution}</span>
                      </li>
                    ))}
                  </ol>
                </div>

                {/* Settings Recommendation */}
                {analysis.settingsRecommendation && (
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-3">Optimal Settings</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {analysis.settingsRecommendation.voltage && (
                        <div>
                          <div className="text-xs text-gray-600">Voltage</div>
                          <div className="text-lg font-bold text-orange-600">
                            {analysis.settingsRecommendation.voltage}
                          </div>
                        </div>
                      )}
                      {analysis.settingsRecommendation.amperage && (
                        <div>
                          <div className="text-xs text-gray-600">Amperage</div>
                          <div className="text-lg font-bold text-orange-600">
                            {analysis.settingsRecommendation.amperage}
                          </div>
                        </div>
                      )}
                      {analysis.settingsRecommendation.wireSpeed && (
                        <div>
                          <div className="text-xs text-gray-600">Wire Speed</div>
                          <div className="text-lg font-bold text-orange-600">
                            {analysis.settingsRecommendation.wireSpeed}
                          </div>
                        </div>
                      )}
                      {analysis.settingsRecommendation.technique && (
                        <div className="col-span-2">
                          <div className="text-xs text-gray-600">Technique Tip</div>
                          <div className="text-sm font-medium text-orange-700 mt-1">
                            {analysis.settingsRecommendation.technique}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Try Again Button */}
                <button
                  onClick={reset}
                  className="w-full px-4 py-2 border-2 border-gray-300 hover:border-orange-500 text-gray-700 hover:text-orange-600 font-medium rounded-lg transition-colors"
                >
                  Analyze Another Weld
                </button>
              </div>
            )}
          </div>
        )}

        {/* Info Banner */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>💡 Pro Tip:</strong> For best results, take a clear, well-lit photo of your weld.
            Include the entire weld bead and surrounding area. Common defects we can identify:
            porosity, spatter, undercut, lack of penetration, cracks, and overlap.
          </p>
        </div>
      </div>
    </div>
  );
};

export default WeldDefectAnalyzer;
