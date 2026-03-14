import React, { createContext, useContext, useState, ReactNode } from 'react';

type Mode = 'beginner' | 'professional';

interface AppContextType {
  currentLogId: string | null;
  setCurrentLogId: (id: string | null) => void;
  currentLogName: string;
  setCurrentLogName: (name: string) => void;
  mode: Mode;
  setMode: (mode: Mode) => void;
}

const AppContext = createContext<AppContextType>({
  currentLogId: null,
  setCurrentLogId: () => {},
  currentLogName: '',
  setCurrentLogName: () => {},
  mode: 'beginner',
  setMode: () => {},
});

export const useAppState = () => useContext(AppContext);

export function AppProvider({ children }: { children: ReactNode }) {
  const [currentLogId, setCurrentLogId] = useState<string | null>(null);
  const [currentLogName, setCurrentLogName] = useState<string>('');
  const [mode, setMode] = useState<Mode>('beginner');

  return (
    <AppContext.Provider
      value={{ currentLogId, setCurrentLogId, currentLogName, setCurrentLogName, mode, setMode }}
    >
      {children}
    </AppContext.Provider>
  );
}
