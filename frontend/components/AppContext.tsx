import React, { createContext, useContext, useState, ReactNode } from 'react';

type Mode = 'beginner' | 'professional';
type AnalysisType = 'quick' | 'full';

interface UploadProgress {
  isUploading: boolean;
  progress: number;
  status: string;
  filename?: string;
}

interface BackgroundTask {
  id: string;
  type: 'report' | 'export' | 'analysis';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  result?: any;
}

interface AppContextType {
  currentLogId: string | null;
  setCurrentLogId: (id: string | null) => void;
  currentLogName: string;
  setCurrentLogName: (name: string) => void;
  mode: Mode;
  setMode: (mode: Mode) => void;
  analysisType: AnalysisType;
  setAnalysisType: (type: AnalysisType) => void;
  uploadProgress: UploadProgress;
  setUploadProgress: (progress: UploadProgress) => void;
  backgroundTasks: BackgroundTask[];
  addBackgroundTask: (task: BackgroundTask) => void;
  updateBackgroundTask: (id: string, updates: Partial<BackgroundTask>) => void;
  removeBackgroundTask: (id: string) => void;
}

const defaultUploadProgress: UploadProgress = {
  isUploading: false,
  progress: 0,
  status: '',
};

const AppContext = createContext<AppContextType>({
  currentLogId: null,
  setCurrentLogId: () => {},
  currentLogName: '',
  setCurrentLogName: () => {},
  mode: 'beginner',
  setMode: () => {},
  analysisType: 'quick',
  setAnalysisType: () => {},
  uploadProgress: defaultUploadProgress,
  setUploadProgress: () => {},
  backgroundTasks: [],
  addBackgroundTask: () => {},
  updateBackgroundTask: () => {},
  removeBackgroundTask: () => {},
});

export const useAppState = () => useContext(AppContext);

export function AppProvider({ children }: { children: ReactNode }) {
  const [currentLogId, setCurrentLogId] = useState<string | null>(null);
  const [currentLogName, setCurrentLogName] = useState<string>('');
  const [mode, setMode] = useState<Mode>('beginner');
  const [analysisType, setAnalysisType] = useState<AnalysisType>('quick');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>(defaultUploadProgress);
  const [backgroundTasks, setBackgroundTasks] = useState<BackgroundTask[]>([]);

  const addBackgroundTask = (task: BackgroundTask) => {
    setBackgroundTasks(prev => [...prev, task]);
  };

  const updateBackgroundTask = (id: string, updates: Partial<BackgroundTask>) => {
    setBackgroundTasks(prev =>
      prev.map(t => (t.id === id ? { ...t, ...updates } : t))
    );
  };

  const removeBackgroundTask = (id: string) => {
    setBackgroundTasks(prev => prev.filter(t => t.id !== id));
  };

  return (
    <AppContext.Provider
      value={{
        currentLogId,
        setCurrentLogId,
        currentLogName,
        setCurrentLogName,
        mode,
        setMode,
        analysisType,
        setAnalysisType,
        uploadProgress,
        setUploadProgress,
        backgroundTasks,
        addBackgroundTask,
        updateBackgroundTask,
        removeBackgroundTask,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}
