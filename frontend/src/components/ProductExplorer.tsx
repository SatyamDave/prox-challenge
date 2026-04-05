/**
 * Product Explorer - AR-Style Interactive Product View
 * Clickable hotspots on product image with contextual info
 */

import React, { useState } from 'react';
import { X, Info, Zap } from 'lucide-react';

interface Hotspot {
  id: string;
  x: number; // percentage
  y: number; // percentage
  label: string;
  title: string;
  description: string;
  specs?: string[];
  pageRef?: number;
}

const HOTSPOTS: Hotspot[] = [
  {
    id: 'display',
    x: 55,
    y: 25,
    label: 'Digital Display',
    title: 'LCD Control Panel',
    description: 'Shows current welding process, voltage, wire speed, and amperage settings. Navigate through menus using the wire/back buttons.',
    specs: ['Process selection', 'Real-time settings display', 'Error codes'],
    pageRef: 8
  },
  {
    id: 'voltage',
    x: 47,
    y: 48,
    label: 'Voltage',
    title: 'Voltage Control Knob',
    description: 'Adjust welding voltage based on material thickness and welding process. Higher voltage = deeper penetration.',
    specs: ['Range: 15-35V', 'Fine adjustment', 'Process-dependent'],
    pageRef: 15
  },
  {
    id: 'wire-speed',
    x: 58,
    y: 48,
    label: 'Wire Speed',
    title: 'Wire Feed Speed Control',
    description: 'Controls how fast wire feeds through the gun. Higher speed = more amperage. Match to voltage for optimal weld.',
    specs: ['Range: 50-700 IPM', 'Stepless adjustment', 'Auto-sync available'],
    pageRef: 16
  },
  {
    id: 'amperage',
    x: 69,
    y: 48,
    label: 'Amperage',
    title: 'Current Control',
    description: 'Sets maximum welding current. Critical for duty cycle management. Higher amperage requires more cooling time.',
    specs: ['Range: 30-220A', 'Duty cycle dependent', 'Thermal protection'],
    pageRef: 12
  },
  {
    id: 'torch-positive',
    x: 62,
    y: 78,
    label: '+',
    title: 'Torch Positive Terminal',
    description: 'DC+ connection for electrode-positive welding (DCEP). Used for MIG, flux-cored, and some stick electrodes.',
    specs: ['MIG: DCEP', 'Flux-core: DCEP', 'Quick-connect'],
    pageRef: 10
  },
  {
    id: 'torch-negative',
    x: 52,
    y: 78,
    label: '−',
    title: 'Torch Negative Terminal',
    description: 'DC- connection for electrode-negative welding (DCEN). Used for TIG and certain stick electrodes.',
    specs: ['TIG: DCEN', 'Some stick: DCEN', 'Brass connector'],
    pageRef: 10
  },
  {
    id: 'ground',
    x: 72,
    y: 78,
    label: 'Ground',
    title: 'Ground Clamp Terminal',
    description: 'Always connect to workpiece. Completes the electrical circuit. Clean metal contact essential.',
    specs: ['Max distance: 10ft', 'Clean connection required', 'Safety critical'],
    pageRef: 11
  }
];

interface ProductExplorerProps {
  onAskQuestion?: (question: string) => void;
}

const ProductExplorer: React.FC<ProductExplorerProps> = ({ onAskQuestion }) => {
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);
  const [showLabels, setShowLabels] = useState(true);

  const handleHotspotClick = (hotspot: Hotspot) => {
    setSelectedHotspot(hotspot);
  };

  const askAboutComponent = (hotspot: Hotspot) => {
    if (onAskQuestion) {
      onAskQuestion(`Tell me more about the ${hotspot.label.toLowerCase()} and when I should adjust it`);
    }
  };

  return (
    <div className="w-full bg-gradient-to-br from-gray-900 via-gray-800 to-orange-900 rounded-xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="bg-orange-500 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Zap className="w-6 h-6 text-white" />
          <h2 className="text-xl font-bold text-white">Interactive Product Explorer</h2>
        </div>
        <button
          onClick={() => setShowLabels(!showLabels)}
          className="px-3 py-1 bg-white/20 hover:bg-white/30 text-white text-sm rounded-lg transition-colors"
        >
          {showLabels ? 'Hide Labels' : 'Show Labels'}
        </button>
      </div>

      {/* Product Image with Hotspots */}
      <div className="relative p-8">
        <div className="relative max-w-3xl mx-auto">
          <img
            src="/product.webp"
            alt="Vulcan OmniPro 220"
            className="w-full h-auto rounded-lg shadow-2xl"
          />

          {/* Hotspot Markers */}
          {HOTSPOTS.map((hotspot) => (
            <button
              key={hotspot.id}
              onClick={() => handleHotspotClick(hotspot)}
              className="absolute transform -translate-x-1/2 -translate-y-1/2 group"
              style={{ left: `${hotspot.x}%`, top: `${hotspot.y}%` }}
            >
              {/* Pulse ring */}
              <div className="absolute inset-0 animate-ping">
                <div className="w-8 h-8 rounded-full bg-orange-400 opacity-75"></div>
              </div>

              {/* Main marker */}
              <div className={`relative w-8 h-8 rounded-full ${
                selectedHotspot?.id === hotspot.id
                  ? 'bg-orange-500 ring-4 ring-orange-300'
                  : 'bg-orange-500 ring-2 ring-orange-300'
              } shadow-lg transition-all group-hover:scale-125 flex items-center justify-center`}>
                <Info className="w-4 h-4 text-white" />
              </div>

              {/* Label */}
              {showLabels && (
                <div className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                  <div className="bg-black/80 text-white text-xs px-2 py-1 rounded shadow-lg">
                    {hotspot.label}
                  </div>
                </div>
              )}
            </button>
          ))}
        </div>

        {/* Info Panel */}
        {selectedHotspot && (
          <div className="absolute top-4 right-4 w-80 bg-white rounded-xl shadow-2xl overflow-hidden animate-in slide-in-from-right">
            <div className="bg-gradient-to-r from-orange-500 to-orange-600 px-4 py-3 flex items-center justify-between">
              <h3 className="font-bold text-white">{selectedHotspot.title}</h3>
              <button
                onClick={() => setSelectedHotspot(null)}
                className="text-white hover:bg-white/20 rounded p-1 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              <p className="text-sm text-gray-700">{selectedHotspot.description}</p>

              {selectedHotspot.specs && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-900 mb-2">Key Specs:</h4>
                  <ul className="space-y-1">
                    {selectedHotspot.specs.map((spec, idx) => (
                      <li key={idx} className="text-xs text-gray-600 flex items-start">
                        <span className="text-orange-500 mr-2">•</span>
                        {spec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedHotspot.pageRef && (
                <div className="text-xs text-gray-500 pt-2 border-t border-gray-200">
                  📄 Manual reference: Page {selectedHotspot.pageRef}
                </div>
              )}

              <button
                onClick={() => askAboutComponent(selectedHotspot)}
                className="w-full px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                <Zap className="w-4 h-4" />
                <span>Ask AI About This</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="px-6 py-4 bg-black/20 text-white text-sm">
        <p>
          <strong>💡 Tip:</strong> Click on the orange markers to learn about each component.
          This interactive view helps you understand your welder before you start welding.
        </p>
      </div>
    </div>
  );
};

export default ProductExplorer;
