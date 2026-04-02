import { create } from 'zustand';

export type ActiveView = 'supply-map' | 'heatmap' | 'road-network' | 'alerts';

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
  
  // Actions
  setActiveView: (view: ActiveView) => void;
  selectCell: (cellId: string | null) => void;
  toggleLayer: (layer: keyof LayerVisibility) => void;
  setDrawerOpen: (isOpen: boolean) => void;
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
}));
