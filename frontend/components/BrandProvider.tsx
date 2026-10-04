"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import BrandIntro from "./BrandIntro";

interface BrandContextType {
  hasSeenIntro: boolean;
  replayIntro: () => void;
  playIntroTransition: (callback?: () => void) => void;
  isIntroPlaying: boolean;
}

const BrandContext = createContext<BrandContextType>({
  hasSeenIntro: false,
  replayIntro: () => {},
  playIntroTransition: () => {},
  isIntroPlaying: false,
});

export const useBrand = () => useContext(BrandContext);

export default function BrandProvider({ children }: { children: React.ReactNode }) {
  // Start as true on first mount so the intro covers the screen before the page renders
  const [isIntroPlaying, setIsIntroPlaying] = useState<boolean>(true);
  const [forceShow, setForceShow] = useState<boolean>(false);
  const [introCallback, setIntroCallback] = useState<(() => void) | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      let seen: string | null = null;
      try { seen = sessionStorage.getItem("apex_intro_seen"); } catch { /* Private browsing may block storage. */ }
      if (seen && !forceShow) {
        setIsIntroPlaying(false);
      } else {
        setIsIntroPlaying(true);
      }
    }
  }, [forceShow]);

  const replayIntro = useCallback(() => {
    try {
      sessionStorage.removeItem("apex_intro_seen");
    } catch {
      // Ignore
    }
    setForceShow(true);
    setIsIntroPlaying(true);
  }, []);

  const playIntroTransition = useCallback((callback?: () => void) => {
    if (callback) {
      setIntroCallback(() => callback);
    }
    setForceShow(true);
    setIsIntroPlaying(true);
  }, []);

  const handleIntroComplete = useCallback(() => {
    setIsIntroPlaying(false);
    setForceShow(false);
    if (introCallback) {
      const cb = introCallback;
      setIntroCallback(null);
      cb();
    }
  }, [introCallback]);

  return (
    <BrandContext.Provider
      value={{
        hasSeenIntro: !isIntroPlaying,
        replayIntro,
        playIntroTransition,
        isIntroPlaying,
      }}
    >
      {isIntroPlaying && (
        <BrandIntro onComplete={handleIntroComplete} forceShow={forceShow} />
      )}
      {children}
    </BrandContext.Provider>
  );
}
