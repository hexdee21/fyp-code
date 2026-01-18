import React, { useCallback } from "react";
import Particles from "react-tsparticles";
import { loadFull } from "tsparticles";

export default function NetworkBackground() {
  const particlesInit = useCallback(async (engine) => {
    await loadFull(engine);
  }, []);

  return (
    <Particles
      init={particlesInit}
      options={{
        fullScreen: false,
        background: { color: "#020617" },
        fpsLimit: 60,
        detectRetina: true,

        particles: {
          number: {
            value: 100,
            density: { enable: true, area: 900 },
          },
          color: { value: "#7dd3fc" },
          shape: { type: "circle" },
          opacity: { value: 1 },     // ✅ FULL
          size: { value: 2.8 },      // ✅ VISIBLE

          links: {
            enable: true,
            distance: 150,
            color: "#38bdf8",
            opacity: 0.5,
            width: 1,
          },

          move: {
            enable: true,
            speed: 0.3,
            outModes: "out",
          },
        },
      }}
      style={{
        width: "100%",
        height: "100%",
        position: "absolute",
        inset: 0,
      }}
    />
  );
}
