import { create } from 'zustand';
import type { AnalysisResponse } from './types';

export type CameraStage = 'exterior' | 'flying-in' | 'cockpit';

interface AppState {
  data: AnalysisResponse | null;
  loading: boolean;
  error: string | null;
  stage: CameraStage;
  panelOpen: boolean;
  activeTab: 'overview' | 'spend' | 'subs' | 'coach' | 'tx';
  coachText: string | null;
  coachLoading: boolean;

  setData: (d: AnalysisResponse | null) => void;
  setLoading: (b: boolean) => void;
  setError: (e: string | null) => void;
  setStage: (s: CameraStage) => void;
  setPanelOpen: (b: boolean) => void;
  setActiveTab: (t: AppState['activeTab']) => void;
  setCoachText: (t: string | null) => void;
  setCoachLoading: (b: boolean) => void;
  flyToCockpit: () => void;
}

export const useStore = create<AppState>((set, get) => ({
  data: null,
  loading: false,
  error: null,
  stage: 'exterior',
  panelOpen: false,
  activeTab: 'overview',
  coachText: null,
  coachLoading: false,

  setData: (d) => set({ data: d }),
  setLoading: (b) => set({ loading: b }),
  setError: (e) => set({ error: e }),
  setStage: (s) => set({ stage: s }),
  setPanelOpen: (b) => set({ panelOpen: b }),
  setActiveTab: (t) => set({ activeTab: t }),
  setCoachText: (t) => set({ coachText: t }),
  setCoachLoading: (b) => set({ coachLoading: b }),

  flyToCockpit: () => {
    const { stage } = get();
    if (stage !== 'exterior') return;
    set({ stage: 'flying-in' });
    // Reveal HUD as the camera lands
    setTimeout(() => set({ stage: 'cockpit', panelOpen: true }), 2400);
  },
}));
