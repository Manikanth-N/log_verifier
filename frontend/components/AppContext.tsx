import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type VerificationMode = 'beginner' | 'pro' | 'certified';

export interface VerificationStatus {
  status: 'none' | 'pass' | 'fail' | 'pending';
  message?: string;
  hashChainValid?: boolean;
  signatureValid?: boolean;
  algorithm?: string;
  chunksVerified?: number;
  totalChunks?: number;
}

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
  verificationMode: VerificationMode;
  setVerificationMode: (mode: VerificationMode) => void;
  verificationStatus: VerificationStatus;
  setVerificationStatus: (status: VerificationStatus) => void;
  publicKeyPath: string | null;
  setPublicKeyPath: (path: string | null) => void;
  publicKeyName: string;
  setPublicKeyName: (name: string) => void;
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

const defaultVerificationStatus: VerificationStatus = {
  status: 'none',
};

const AppContext = createContext<AppContextType>({
  currentLogId: null,
  setCurrentLogId: () => {},
  currentLogName: '',
  setCurrentLogName: () => {},
  verificationMode: 'pro',
  setVerificationMode: () => {},
  verificationStatus: defaultVerificationStatus,
  setVerificationStatus: () => {},
  publicKeyPath: null,
  setPublicKeyPath: () => {},
  publicKeyName: '',
  setPublicKeyName: () => {},
  uploadProgress: defaultUploadProgress,
  setUploadProgress: () => {},
  backgroundTasks: [],
  addBackgroundTask: () => {},
  updateBackgroundTask: () => {},
  removeBackgroundTask: () => {},
});

export const useAppState = () => useContext(AppContext);

const VERIFICATION_MODE_KEY = 'telemetry_verification_mode';
const PUBLIC_KEY_PATH_KEY = 'telemetry_public_key_path';
const PUBLIC_KEY_NAME_KEY = 'telemetry_public_key_name';

export function AppProvider({ children }: { children: ReactNode }) {
  const [currentLogId, setCurrentLogId] = useState<string | null>(null);
  const [currentLogName, setCurrentLogName] = useState<string>('');
  const [verificationMode, setVerificationModeState] = useState<VerificationMode>('pro');
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus>(defaultVerificationStatus);
  const [publicKeyPath, setPublicKeyPathState] = useState<string | null>(null);
  const [publicKeyName, setPublicKeyNameState] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>(defaultUploadProgress);
  const [backgroundTasks, setBackgroundTasks] = useState<BackgroundTask[]>([]);

  // Load persisted settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const [savedMode, savedKeyPath, savedKeyName] = await AsyncStorage.multiGet([
          VERIFICATION_MODE_KEY,
          PUBLIC_KEY_PATH_KEY,
          PUBLIC_KEY_NAME_KEY,
        ]);
        if (savedMode[1]) {
          setVerificationModeState(savedMode[1] as VerificationMode);
        }
        if (savedKeyPath[1]) {
          setPublicKeyPathState(savedKeyPath[1]);
        }
        if (savedKeyName[1]) {
          setPublicKeyNameState(savedKeyName[1]);
        }
      } catch (e) {
        console.error('Failed to load settings:', e);
      }
    };
    loadSettings();
  }, []);

  // Persist verification mode
  const setVerificationMode = async (mode: VerificationMode) => {
    setVerificationModeState(mode);
    try {
      await AsyncStorage.setItem(VERIFICATION_MODE_KEY, mode);
    } catch (e) {
      console.error('Failed to save mode:', e);
    }
  };

  // Persist public key path
  const setPublicKeyPath = async (path: string | null) => {
    setPublicKeyPathState(path);
    try {
      if (path) {
        await AsyncStorage.setItem(PUBLIC_KEY_PATH_KEY, path);
      } else {
        await AsyncStorage.removeItem(PUBLIC_KEY_PATH_KEY);
      }
    } catch (e) {
      console.error('Failed to save public key path:', e);
    }
  };

  // Persist public key name
  const setPublicKeyName = async (name: string) => {
    setPublicKeyNameState(name);
    try {
      if (name) {
        await AsyncStorage.setItem(PUBLIC_KEY_NAME_KEY, name);
      } else {
        await AsyncStorage.removeItem(PUBLIC_KEY_NAME_KEY);
      }
    } catch (e) {
      console.error('Failed to save public key name:', e);
    }
  };

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
        verificationMode,
        setVerificationMode,
        verificationStatus,
        setVerificationStatus,
        publicKeyPath,
        setPublicKeyPath,
        publicKeyName,
        setPublicKeyName,
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
