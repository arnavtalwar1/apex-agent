"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import BrandIntro from "./BrandIntro";

interface BrandContextType {
  hasSeenIntro: boolean;
  replayIntro: () => void;
}

const BrandContext = createContext<BrandContextType>({
  hasSeenIntro: true,
  replayIntro: () => {},
});

export const useBrand = () => useContext(BrandContext);

export default function BrandProvider({ children }: { children: React.ReactNode }) {
  const [hasSeenIntro, setHasSeenIntro] = useState(true);
  const [forceShow, setForceShow] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const seen = sessionStorage.getItem("apex_intro_seen");
      if (!seen) {
        setHasSeenIntro(false);
      }
    }
  }, []);

  const replayIntro = () => {
    try {
      sessionStorage.removeItem("apex_intro_seen");
    } catch {
      // Ignore in private modes
    }
    setHasSeenIntro(false);
    setForceShow(true);
  };

  const handleIntroComplete = () => {
    setHasSeenIntro(true);
    setForceShow(false);
  };

  return (
    <BrandContext.Provider value={{ hasSeenIntro, replayIntro }}>
      {!hasSeenIntro && (
        <BrandIntro onComplete={handleIntroComplete} forceShow={forceShow} />
      )}
      {children}
    </BrandContext.Provider>
  );
}
