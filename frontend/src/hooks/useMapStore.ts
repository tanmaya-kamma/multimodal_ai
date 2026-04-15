import { create } from 'zustand';
import { RouteAnalysisResponse } from '../lib/types';

export type ActiveView = 'supply-map' | 'heatmap' | 'road-network' | 'alerts' | 'command-center';

interface LayerVisibility {
  boundary: boolean;
  majorRoads: boolean;
  secondaryRoads: boolean;
  railways: boolean;
  heatmap: boolean;
  pois: boolean;
}

interface MapState {
  activeView: ActiveView;
  selectedCell: string | null;
  isDrawerOpen: boolean;
  layerVisibility: LayerVisibility;
  showRoutePanel: boolean;
  routeData: RouteAnalysisResponse | null;
  showSimPanel: boolean;
  showLayerPanel: boolean;
  
  // Actions
  setActiveView: (view: ActiveView) => void;
  selectCell: (cellId: string | null) => void;
  toggleLayer: (layer: keyof LayerVisibility) => void;
  setDrawerOpen: (isOpen: boolean) => void;
  toggleRoutePanel: () => void;
  setRouteData: (data: RouteAnalysisResponse | null) => void;
  toggleSimPanel: () => void;
  toggleLayerPanel: () => void;
}

const defaultLayers: LayerVisibility = {
  boundary: true,
  majorRoads: true,
  secondaryRoads: true,
  railways: true,
  heatmap: false,
  pois: true,
};

export const useMapStore = create<MapState>((set) => ({
  activeView: 'supply-map',
  selectedCell: null,
  isDrawerOpen: false,
  layerVisibility: { ...defaultLayers },
  showRoutePanel: false,
  routeData: null,
  showSimPanel: false,
  showLayerPanel: false,
  
  setActiveView: (view: ActiveView) => set((state) => {
    // Automatically adjust layers based on the view
    const newLayers = { ...state.layerVisibility };
    
    if (view === 'heatmap') {
      newLayers.heatmap = true;
    } else if (view === 'supply-map') {
      newLayers.heatmap = false;
      newLayers.pois = true;
    } else if (view === 'road-network') {
      newLayers.heatmap = false;
      newLayers.majorRoads = true;
      newLayers.secondaryRoads = true;
    } else if (view === 'command-center') {
      // Command center shows everything — heatmap + POIs + roads
      newLayers.heatmap = true;
      newLayers.pois = true;
      newLayers.majorRoads = true;
    }
    
    return { activeView: view, layerVisibility: newLayers };
  }),
  
  selectCell: (cellId: string | null) => set({ 
    selectedCell: cellId,
    isDrawerOpen: !!cellId
  }),
  
  setDrawerOpen: (isOpen: boolean) => set((state) => ({ 
    isDrawerOpen: isOpen,
    // if drawer is closed by user, clear the cell selection
    selectedCell: isOpen ? state.selectedCell : null
  })),
  
  toggleLayer: (layer) => set((state) => ({
    layerVisibility: {
      ...state.layerVisibility,
      [layer]: !state.layerVisibility[layer]
    }
  })),

  toggleRoutePanel: () => set((state) => ({ 
    showRoutePanel: !state.showRoutePanel,
    // Close other panels when opening routes
    showSimPanel: false,
    showLayerPanel: false,
  })),
  
  setRouteData: (data) => set({ routeData: data }),
  
  toggleSimPanel: () => set((state) => ({ 
    showSimPanel: !state.showSimPanel,
    // Close other panels when opening sim
    showRoutePanel: false,
    showLayerPanel: false,
  })),
  
  toggleLayerPanel: () => set((state) => ({
    showLayerPanel: !state.showLayerPanel,
    // Close other panels when opening layers
    showRoutePanel: false,
    showSimPanel: false,
  })),
}));
