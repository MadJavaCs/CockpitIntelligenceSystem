const BACKEND_ENDPOINT = "/api/dashboard-state";
const HOME_ASSISTANT_ENDPOINT = "/api/home-assistant-context";
const HOME_ASSISTANT_TRIGGER_ENDPOINT = "http://127.0.0.1:8001/trigger-home-assistant";
const MQTT_LAST_EVENT_ENDPOINT = "http://127.0.0.1:8001/mqtt/last-event";

const FALLBACK_DATA = {
  system: {
    online: true,
    overrideMode: false,
    systemLabel: "System Online",
  },
  time: {
    clock: "22:14",
    date: "13 April 2026",
    phase: "Night Operation",
  },
  context: {
    drivingContext: "Nachtfahrt",
    criticalManeuver: "none",
    weather: "Nebel",
    timeOfDay: "night",
    isNight: true,
    timeSource: "system_time",
    homeAssistantConnected: false,
    smartContextStatus: "Smart Context: Local Sync",
    route: "A8 Urban Exit",
    traffic: "Moderat",
    homeAssistant: "Naechster Termin 10:00",
    weatherSensor: "Visibility reduced",
  },
  telemetry: {
    stress: 38,
    energy: 61,
    focus: 57,
    heartRate: 82,
    cameraStatus: "Eyes On Road",
    wheelContact: "Stable",
    cabinState: "Low Noise",
    inputSummary: "Context adaptation active",
  },
  assessment: {
    driverState: "Muede",
    mode: "Wachsamkeit",
    riskScore: 64,
    heartRateState: "normal",
    sensorModifier: 0,
    criticalManeuverState: "none",
    criticalManeuverImpact: 0,
    warningLevel: "ORANGE",
    recommendation: "Aufmerksamkeit aktiv halten und bei ersten Ermuedungszeichen Pause machen.",
    reason: "Nachtfahrt mit sinkender Energie verlangt eine aufmerksamkeitsorientierte Begleitung.",
    assistReaction: "Wachsamkeitswarnung",
    lightMode: "Aktivierungslicht",
    aiTitle: "Adaptive Support Strategy",
    aiSummary: "System priorisiert ruhige Hinweise, reduzierte Reizdichte und fruehzeitige Pausenempfehlung.",
    coffeeRecommendation: "Optional",
    coffeeReason: "Kaffee kann unterstuetzen, ersetzt aber keine Pause.",
    warningTitle: "Elevated Attention",
    warningPriority: "Medium",
    warningTrigger: "Night fatigue pattern",
    warningAction: "Pause in 15 min pruefen",
  },
};

let currentDataset = null;
let baseSystemDataset = null;
let scanAnimationFrame = null;
let lastHomeAssistantTriggerKey = null;
let previousRenderedRiskScore = null;
let backendRuntimeState = "online";
let mqttRuntimeState = "simulated";
let lastDebugEventTime = "-";
let runtimeEvents = [];
let stateValueAnimation = {
  frameId: null,
  completionTimer: null,
};

const STATE_VALUE_ANIMATION_DURATION = 900;

function sanitizePercent(value) {
  return Math.max(0, Math.min(100, Number(value) || 0));
}

function deriveDistractionState(focus) {
  const safeFocus = sanitizePercent(focus);

  if (safeFocus < 30) {
    return { state: "stark abgelenkt", riskModifier: 15 };
  }

  if (safeFocus < 60) {
    return { state: "abgelenkt", riskModifier: 8 };
  }

  return { state: "keine Ablenkung", riskModifier: 0 };
}

function deriveDistractionPresentation(focus, assessment = {}) {
  const fallback = deriveDistractionState(focus);
  const state = fallback.state;
  const riskModifier = fallback.riskModifier;
  const isActive = riskModifier > 0;
  const normalizedState = state.trim().toLowerCase();
  const badgeState = normalizedState === "stark abgelenkt"
    ? "high"
    : normalizedState === "abgelenkt"
      ? "medium"
      : "none";

  return {
    state,
    riskModifier,
    isActive,
    badgeState,
    label: `Ablenkung: ${state} (${riskModifier >= 0 ? "+" : ""}${riskModifier})`,
  };
}

function sanitizeHeartRate(value) {
  return Math.max(60, Math.min(130, Number(value) || 60));
}

function deriveHeartRateSensorState(heartRate) {
  const safeHeartRate = sanitizeHeartRate(heartRate);

  if (safeHeartRate > 105) {
    return {
      bpm: safeHeartRate,
      state: "kritisch erhoeht",
      uiState: "critical",
      statusLabel: "Critical",
      riskModifier: 15,
      label: `Heart Rate ${safeHeartRate} bpm / kritisch erhoeht / +15 Risk`,
      analysisLabel: `Heart Rate: ${safeHeartRate} bpm -> Critical -> Risk +15`,
      impactLabel: "Impact on Risk: +15",
    };
  }

  if (safeHeartRate >= 86) {
    return {
      bpm: safeHeartRate,
      state: "erhoeht",
      uiState: "elevated",
      statusLabel: "Elevated",
      riskModifier: 8,
      label: `Heart Rate ${safeHeartRate} bpm / erhoeht / +8 Risk`,
      analysisLabel: `Heart Rate: ${safeHeartRate} bpm -> Elevated -> Risk +8`,
      impactLabel: "Impact on Risk: +8",
    };
  }

  return {
    bpm: safeHeartRate,
    state: "normal",
    uiState: "normal",
    statusLabel: "Normal",
    riskModifier: 0,
    label: `Heart Rate ${safeHeartRate} bpm / normal / +0 Risk`,
    analysisLabel: `Heart Rate: ${safeHeartRate} bpm -> Normal -> kein zusaetzlicher Risk Impact`,
    impactLabel: "Impact on Risk: +0",
  };
}

function deriveConsistentHeartRate(heartRate, riskScore, driverState) {
  const parsedHeartRate = Number(heartRate);

  if (Number.isFinite(parsedHeartRate)) {
    return sanitizeHeartRate(parsedHeartRate);
  }

  return deriveSimulatedHeartRate({
    stress: 50,
    riskScore,
    driverState,
  });
}

function deriveSimulatedHeartRate({ stress, riskScore, driverState }) {
  const safeStress = sanitizePercent(stress);
  const safeRiskScore = sanitizePercent(riskScore);
  const normalizedState = String(driverState || "").trim().toLowerCase();
  const baseHeartRate = randomInt(60, 100);
  let stressAdjustment = 0;

  if (safeStress >= 75) {
    stressAdjustment += randomInt(4, 8);
  } else if (safeStress >= 50) {
    stressAdjustment += randomInt(1, 5);
  } else if (safeStress <= 20) {
    stressAdjustment -= randomInt(0, 4);
  }

  if (safeRiskScore >= 65 || normalizedState === "kritisch") {
    stressAdjustment += randomInt(2, 7);
  } else if (safeRiskScore >= 35 || normalizedState === "muede") {
    stressAdjustment += randomInt(-1, 4);
  } else {
    stressAdjustment += randomInt(-3, 2);
  }

  const sensorVariance = randomInt(-10, 10);
  return sanitizeHeartRate(baseHeartRate + stressAdjustment + sensorVariance);
}

function deriveCriticalManeuverState(criticalManeuver) {
  const normalizedManeuver = String(criticalManeuver || "none").trim().toLowerCase();

  if (normalizedManeuver === "overtaking") {
    return {
      key: "overtaking",
      label: "Ueberholen",
      riskModifier: 12,
      analysisLabel: "Kritisches Fahrmanoever erkannt -> erhoehte Aufmerksamkeit erforderlich",
      strategyText: "Mirror Check | Blind Spot Awareness | Tempo stabilisieren",
    };
  }

  if (normalizedManeuver === "intersection") {
    return {
      key: "intersection",
      label: "Kreuzung",
      riskModifier: 9,
      analysisLabel: "Kritisches Fahrmanoever erkannt -> erhoehte Aufmerksamkeit erforderlich",
      strategyText: "Kreuzungsbereich bewusst scannen | Vorfahrt pruefen",
    };
  }

  if (normalizedManeuver === "lane_change") {
    return {
      key: "lane_change",
      label: "Spurwechsel",
      riskModifier: 7,
      analysisLabel: "Kritisches Fahrmanoever erkannt -> erhoehte Aufmerksamkeit erforderlich",
      strategyText: "Spiegel pruefen | Schulterblick | Abstand stabil halten",
    };
  }

  if (normalizedManeuver === "turn") {
    return {
      key: "turn",
      label: "Abbiegen",
      riskModifier: 5,
      analysisLabel: "Kritisches Fahrmanoever erkannt -> erhoehte Aufmerksamkeit erforderlich",
      strategyText: "Abbiegebereich pruefen | Geschwindigkeit reduzieren | Querverkehr beachten",
    };
  }

  return {
    key: "none",
    label: "Kein kritisches Manoever",
    riskModifier: 0,
    analysisLabel: "",
    strategyText: "",
  };
}

function deriveAwarenessBoostState(heartRateState, criticalManeuver) {
  const normalizedHeartRateState = String(heartRateState || "normal").trim().toLowerCase();
  const maneuverState = deriveCriticalManeuverState(criticalManeuver);

  if (maneuverState.key === "none") {
    return {
      riskModifier: 0,
      analysisLabel: "",
      label: "",
    };
  }

  if (normalizedHeartRateState === "kritisch erhoeht") {
    return {
      riskModifier: ["turn", "intersection"].includes(maneuverState.key) ? 10 : 8,
      analysisLabel: "Sensor + Fahrmanoever Kombination erkannt -> erhoehte Entscheidungsbelastung",
      label: `Awareness Boost (${maneuverState.label})`,
    };
  }

  if (normalizedHeartRateState === "erhoeht") {
    return {
      riskModifier: maneuverState.key === "lane_change" ? 5 : 6,
      analysisLabel: "Sensor + Fahrmanoever Kombination erkannt -> erhoehte Entscheidungsbelastung",
      label: `Awareness Boost (${maneuverState.label})`,
    };
  }

  return {
    riskModifier: 0,
    analysisLabel: "",
    label: "",
  };
}

function deriveNightRiskModifier(isNight, energy, focus) {
  if (!isNight) return 0;
  return energy <= 50 || focus <= 50 ? 6 : 4;
}

function deriveWeatherRiskModifier(weather, stress, focus) {
  const weatherLabel = String(weather || "").trim().toLowerCase();

  if (weatherLabel.includes("sturm")) return 10;
  if (weatherLabel.includes("nebel")) return focus < 60 ? 8 : 6;
  if (weatherLabel.includes("regen")) return stress >= 65 ? 6 : 4;
  if (weatherLabel.includes("wind")) return 3;
  return 0;
}

function deriveDriverStateFromRisk(riskScore, options = {}) {
  const safeRiskScore = sanitizePercent(riskScore);
  const stress = sanitizePercent(options.stress ?? 50);
  const energy = sanitizePercent(options.energy ?? 60);
  const focus = sanitizePercent(options.focus ?? 60);
  const previousState = String(options.previousState || "").trim().toLowerCase();
  const riskTrend = options.riskTrend || "stable";
  const isRising = riskTrend === "rising";
  const isFalling = riskTrend === "falling" || riskTrend === "decreasing";
  const heartRateState = String(options.heartRateState || "normal").trim().toLowerCase();
  const weatherLabel = String(options.weather || "").trim().toLowerCase();
  const isNight = Boolean(options.isNight);
  let contextPressure = 0;

  if (stress >= 75) contextPressure += 5;
  if (energy <= 35) contextPressure += 5;
  if (focus <= 40) contextPressure += 6;
  if (heartRateState === "kritisch erhoeht") contextPressure += 8;
  else if (heartRateState === "erhoeht") contextPressure += 5;
  if (isNight) contextPressure += 4;
  if (weatherLabel.includes("nebel")) contextPressure += 4;

  const effectiveRisk = sanitizePercent(safeRiskScore + contextPressure);
  const severeSignal = stress >= 82 || focus <= 30 || heartRateState === "kritisch erhoeht";
  const fatigueSignal = energy <= 42 && focus <= 55;
  let state = "Wachsam";

  if (previousState === "kritisch") {
    state = safeRiskScore >= 58 || severeSignal || (effectiveRisk >= 62 && !isFalling)
      ? "Kritisch"
      : safeRiskScore >= 35 || fatigueSignal
        ? "Muede"
        : "Wachsam";
  } else if (previousState === "muede") {
    state = effectiveRisk >= 68 && (isRising || severeSignal)
      ? "Kritisch"
      : safeRiskScore >= 30 || fatigueSignal || (isNight && weatherLabel.includes("nebel"))
        ? "Muede"
        : "Wachsam";
  } else if (effectiveRisk >= 68 && (isRising || severeSignal || safeRiskScore >= 72)) {
    state = "Kritisch";
  } else if (effectiveRisk >= 38 || fatigueSignal) {
    state = "Muede";
  }

  if (state === "Kritisch") {
    return {
      riskScore: safeRiskScore,
      state: "Kritisch",
      badge: "Kritisch",
      theme: "red",
      warningLevel: "ROT",
    };
  }

  if (state === "Muede") {
    return {
      riskScore: safeRiskScore,
      state: "Muede",
      badge: "Muede",
      theme: "orange",
      warningLevel: "ORANGE",
    };
  }

  return {
    riskScore: safeRiskScore,
    state: "Wachsam",
    badge: "Wachsam",
    theme: "green",
    warningLevel: "GRUEN",
  };
}

function deriveAssistReactionFromState(driverState, focus, assessment = {}) {
  const normalizedState = String(driverState || "").trim().toLowerCase();
  const distraction = deriveDistractionPresentation(focus, assessment);
  const hasDistraction = distraction.badgeState !== "none";

  if (normalizedState === "kritisch") {
    if (hasDistraction) {
      return {
        assistReaction: "Pause + Fokuswarnung",
        reason: "Hohe Belastung erkannt. Das System priorisiert Pause und Aufmerksamkeitsrueckfuehrung.",
      };
    }

    return {
      assistReaction: "Pause + Warnsystem",
      reason: "Hohe Belastung erkannt. Das System aktiviert Warnhinweise und priorisiert eine Pause.",
    };
  }

  if (normalizedState === "muede") {
    if (hasDistraction) {
      return {
        assistReaction: "Fokuslenkung",
        reason: "Mittlere Belastung erkannt. Das System unterstuetzt die Rueckfuehrung der Aufmerksamkeit.",
      };
    }

    return {
      assistReaction: "Wachsamkeitswarnung",
      reason: "Erste Ermuedung erkannt. Das System stabilisiert Wachheit und beobachtet den Zustand weiter.",
    };
  }

  return {
    assistReaction: "Stabiler Zustand",
    reason: "Stabiler Zustand erkannt. Der Fahrer ist wachsam, es sind keine Massnahmen noetig.",
  };
}

function deriveDayNightContext(clockValue) {
  const fallbackNow = new Date();
  const fallbackClock = `${String(fallbackNow.getHours()).padStart(2, "0")}:${String(
    fallbackNow.getMinutes(),
  ).padStart(2, "0")}`;
  const sourceClock = typeof clockValue === "string" && /^\d{2}:\d{2}$/.test(clockValue) ? clockValue : fallbackClock;
  const [hourText, minuteText] = sourceClock.split(":");
  const totalMinutes = (Number(hourText) || 0) * 60 + (Number(minuteText) || 0);
  const isNight = totalMinutes >= 20 * 60 || totalMinutes < 6 * 60;

  return {
    clock: sourceClock,
    isNight,
    timeOfDay: isNight ? "Night" : "Day",
    modeLabel: isNight ? "NIGHT MODE ACTIVE" : "DAY MODE",
    phaseLabel: isNight ? "Night Operation" : "Day Operation",
    influenceLabel: isNight
      ? "Night Influence +10 due to reduced visibility and higher fatigue sensitivity."
      : "Day Influence +0 with standard visibility baseline.",
  };
}

function deriveNightAwareNarrative(dataset, timeContext) {
  const baseMode = dataset.assessment?.mode || "Adaptive";
  const assistNarrative = deriveAssistReactionFromState(
    dataset.assessment?.driverState,
    dataset.telemetry?.focus,
    dataset.assessment,
  );
  const stateReason = dataset.assessment?.reason || assistNarrative.reason;
  const maneuverStrategy = dataset.assessment?.criticalManeuverStrategy || "";

  if (timeContext.isNight) {
    return {
      assistReaction: assistNarrative.assistReaction,
      reason: stateReason,
      recommendation: maneuverStrategy
        ? `Assistenz intensivieren, Warnlicht aktiv halten und bei sinkender Wachheit fruehe Pause empfehlen. ${maneuverStrategy}.`
        : "Assistenz intensivieren, Warnlicht aktiv halten und bei sinkender Wachheit fruehe Pause empfehlen.",
      warningAction: maneuverStrategy
        ? `Nachtkontext aktiv: Fokus sichern. ${maneuverStrategy}.`
        : "Nachtkontext aktiv: Fokus sichern und Pause zeitnah pruefen.",
      aiSummary: maneuverStrategy
        ? `System priorisiert ${baseMode.toLowerCase()} im Nachtkontext mit erhoehter Aufmerksamkeitsfuehrung. ${maneuverStrategy}.`
        : `System priorisiert ${baseMode.toLowerCase()} im Nachtkontext mit erhoehter Aufmerksamkeitsfuehrung.`,
    };
  }

  return {
    assistReaction: assistNarrative.assistReaction,
    reason: stateReason,
    recommendation: dataset.assessment?.recommendation || "Adaptive Unterstuetzung beibehalten.",
    warningAction: dataset.assessment?.warningAction || "Monitoring fortsetzen",
    aiSummary: dataset.assessment?.aiSummary || `System priorisiert ${baseMode.toLowerCase()} im Tageskontext.`,
  };
}

function deriveSystemModeFromDriverState(driverState) {
  const normalizedState = String(driverState || "").trim().toLowerCase();

  if (normalizedState === "kritisch") {
    return { label: "Interventionsmodus", key: "intervention" };
  }

  if (normalizedState === "muede") {
    return { label: "Warnbetrieb", key: "warning" };
  }

  return { label: "Normalbetrieb", key: "normal" };
}

function deriveSystemDecisionFromDriverState(driverState) {
  const normalizedState = String(driverState || "").trim().toLowerCase();

  if (normalizedState === "kritisch") {
    return {
      text: "Systementscheidung: Interventionsmodus aktiviert",
      key: "intervention",
    };
  }

  if (normalizedState === "muede") {
    return {
      text: "Systementscheidung: Warnmodus aktiviert",
      key: "warning",
    };
  }

  return {
    text: "Systementscheidung: Normalbetrieb aktiv",
    key: "normal",
  };
}

function deriveSystemDecisionReason(dataset, derivedState, riskContext) {
  const context = dataset?.context || {};
  const telemetry = dataset?.telemetry || {};
  const factors = [];
  const stress = sanitizePercent(telemetry.stress);
  const energy = sanitizePercent(telemetry.energy);
  const focus = sanitizePercent(telemetry.focus);
  const weather = String(context.weather || "").trim();

  if (stress >= 70) {
    factors.push("Stress hoch");
  } else if (stress <= 25) {
    factors.push("Stress niedrig");
  }

  if (energy <= 35) {
    factors.push("Energy niedrig");
  } else if (energy >= 80) {
    factors.push("Energy hoch");
  }

  if (focus <= 35) {
    factors.push("Focus niedrig");
  } else if (focus >= 80) {
    factors.push("Focus hoch");
  }

  if (context.isNight) {
    factors.push("Nachtkontext");
  } else {
    factors.push("Tagkontext");
  }

  if (context.criticalManeuver && context.criticalManeuver !== "none") {
    factors.push("kritisches Fahrmanoever");
  }

  if (weather && weather !== "Klar") {
    factors.push(weather);
  }

  if (factors.length === 0) {
    factors.push(`Risk ${riskContext.finalRisk}`);
    factors.push(derivedState.state);
  }

  return factors.slice(0, 3).join(", ");
}

function deriveDrivingModePresentation(riskScore) {
  const safeRiskScore = sanitizePercent(riskScore);
  const markerPosition = Math.max(4, Math.min(96, safeRiskScore));

  if (safeRiskScore >= 65) {
    return {
      mode: "Warnmodus",
      markerPosition,
    };
  }

  if (safeRiskScore >= 35) {
    return {
      mode: "Adaptiv",
      markerPosition,
    };
  }

  return {
    mode: "Komfort",
    markerPosition,
  };
}

function deriveDrivingModeFromRisk(riskScore) {
  return deriveDrivingModePresentation(riskScore).mode;
}

function formatDrivingModeDecision(riskIndex, driverState, drivingMode) {
  const stateLabel = {
    muede: "Müde",
    mude: "Müde",
    wachsam: "Wachsam",
    kritisch: "Kritisch",
  }[String(driverState || "").trim().toLowerCase()] || driverState || "Wachsam";
  const modeLabel = String(drivingMode || "Komfort").toLowerCase().includes("modus")
    ? drivingMode
    : `${drivingMode}modus`;
  return `Risk Index ${riskIndex} • ${stateLabel} • ${modeLabel} aktiv`;
}

function deriveSystemCoupling(dataset, derivedState, riskContext, riskTrend) {
  const context = dataset?.context || {};
  const assessment = dataset?.assessment || {};
  const homeAssistantConnected = Boolean(context.homeAssistantConnected)
    || context.timeSource === "home_assistant";
  const stateKey = String(derivedState?.state || "").trim().toLowerCase();
  const riskIndex = sanitizePercent(riskContext?.finalRisk ?? assessment.riskScore);
  const drivingMode = assessment.mode || deriveDrivingModeFromRisk(riskIndex);
  const driverStateLabel = derivedState?.state || "Wachsam";
  const trendKey = riskTrend?.key || "stable";
  const hasCriticalManeuver = assessment.criticalManeuverImpact > 0;
  const focus = sanitizePercent(dataset?.telemetry?.focus);
  const hasLowFocus = focus < 60;
  const syncMode = homeAssistantConnected ? "HA Sync" : "Local Sync";
  const triggerReason = assessment.triggerReason
    || (stateKey === "kritisch"
      ? `Risk ${riskIndex}: kritischer Zustand`
      : hasLowFocus
        ? `Risk ${riskIndex}: niedriger Focus`
        : riskIndex >= 35
          ? `Risk ${riskIndex}: mittlere Belastung`
          : `Risk ${riskIndex}: stabiler Zustand`);
  const attentionStrategy = hasLowFocus ? "Focus Guidance" : "Attention Support";

  if (stateKey === "kritisch") {
    return {
      stateKey,
      riskIndex,
      drivingMode,
      supportLevel: "Intervention",
      strategy: hasCriticalManeuver ? "Intervention Support + Maneuver Guard" : "Intervention Support",
      eventPriority: "High",
      syncMode,
      mqttTopic: "porsche/driver/state/critical",
      mqttStatus: "MQTT Prepared: Critical",
      homeAssistantStatus: homeAssistantConnected ? "HA Sync: Intervention" : "HA Standby",
      homeAssistantLevel: homeAssistantConnected ? "error" : "warn",
      warningTrigger: `${syncMode} / ${triggerReason}`,
      linkedSummary: formatDrivingModeDecision(riskIndex, driverStateLabel, drivingMode),
      recommendation: "Assistenz eskalieren, visuelle Warnung aktiv halten und Pause unmittelbar priorisieren.",
      warningAction: "Intervention aktiv: Pause oder Fahrerwechsel priorisieren",
      aiSummary: `Risk ${riskIndex} aktiviert Intervention ueber ${syncMode}.`,
      coffeeRecommendation: "Break",
      lightMode: "Warnlicht",
      triggerReason,
    };
  }

  if (stateKey === "muede") {
    return {
      stateKey,
      riskIndex,
      drivingMode,
      supportLevel: "Assist",
      strategy: hasCriticalManeuver ? `${attentionStrategy} + Maneuver Guard` : attentionStrategy,
      eventPriority: trendKey === "rising" ? "Medium High" : "Medium",
      syncMode,
      mqttTopic: "porsche/driver/state/attention",
      mqttStatus: "MQTT Prepared: Attention",
      homeAssistantStatus: homeAssistantConnected ? "HA Sync: Assist" : "HA Standby",
      homeAssistantLevel: homeAssistantConnected ? "warn" : "warn",
      warningTrigger: `${syncMode} / ${triggerReason}`,
      linkedSummary: formatDrivingModeDecision(riskIndex, driverStateLabel, drivingMode),
      recommendation: "Aufmerksamkeit stabilisieren, Reizdichte reduzieren und Pause frueh pruefen.",
      warningAction: "Assistenz aktiv: Fokus sichern und Pausenfenster beobachten",
      aiSummary: `Risk ${riskIndex} aktiviert Attention Support ueber ${syncMode}.`,
      coffeeRecommendation: "Optional",
      lightMode: "Aktivierungslicht",
      triggerReason,
    };
  }

  return {
    stateKey,
    riskIndex,
    drivingMode,
    supportLevel: "Monitor",
    strategy: "Passive Monitoring",
    eventPriority: "Low",
    syncMode,
    mqttTopic: "porsche/driver/state/normal",
    mqttStatus: "MQTT Prepared: Normal",
    homeAssistantStatus: homeAssistantConnected ? "HA Sync: Context" : "HA Standby",
    homeAssistantLevel: homeAssistantConnected ? "ok" : "warn",
    warningTrigger: `${syncMode} / ${triggerReason}`,
    linkedSummary: formatDrivingModeDecision(riskIndex, driverStateLabel, drivingMode),
    recommendation: "Stabilen Zustand passiv beobachten und Komfortmodus beibehalten.",
    warningAction: "Monitoring fortsetzen",
    aiSummary: `Risk ${riskIndex} bleibt im Monitoring ueber ${syncMode}.`,
    coffeeRecommendation: "Not needed",
    lightMode: "Komfortlicht",
    triggerReason,
  };
}

function applySystemCouplingToDataset(dataset, coupling) {
  return {
    ...dataset,
    system: {
      ...dataset.system,
      systemLabel: coupling.supportLevel === "Intervention"
        ? "System: Intervention Active"
        : coupling.supportLevel === "Assist"
          ? "System: Assist Active"
          : dataset.system?.systemLabel || "System Online",
    },
    context: {
      ...dataset.context,
      smartContextStatus: dataset.context?.homeAssistantConnected
        ? `Smart Context: ${coupling.homeAssistantStatus}`
        : "Smart Context: Local Sync",
    },
    telemetry: {
      ...dataset.telemetry,
      inputSummary: `${dataset.telemetry?.inputSummary || "Context adaptation active"} / Support ${coupling.supportLevel}`,
    },
    assessment: {
      ...dataset.assessment,
      mode: coupling.drivingMode,
      recommendation: coupling.recommendation,
      warningAction: coupling.warningAction,
      warningTrigger: coupling.warningTrigger,
      aiSummary: coupling.aiSummary,
      coffeeRecommendation: coupling.coffeeRecommendation,
      lightMode: coupling.lightMode,
      supportStrategy: coupling.strategy,
      supportLevel: coupling.supportLevel,
      eventPriority: coupling.eventPriority,
      triggerReason: coupling.triggerReason,
    },
  };
}

function animateStateTransition(elementId, nextStateKey) {
  const element = document.getElementById(elementId);
  if (!element) return;

  const previousStateKey = element.dataset.stateKey;
  element.dataset.stateKey = String(nextStateKey || "");

  if (!previousStateKey || previousStateKey === element.dataset.stateKey) {
    return;
  }

  element.classList.remove("is-state-shift");
  void element.offsetWidth;
  element.classList.add("is-state-shift");
  window.setTimeout(() => element.classList.remove("is-state-shift"), 460);
}

function pulseDataflowActivity(selectors, className = "is-dataflow-sync", duration = 680) {
  selectors.forEach((selector) => {
    const node = document.querySelector(selector);
    if (!node) return;

    node.classList.remove(className);
    void node.offsetWidth;
    node.classList.add(className);
    window.setTimeout(() => node.classList.remove(className), duration);
  });
}

function animateDashboardStateTransition(driverState, riskTrendKey) {
  const stateKey = String(driverState || "").trim().toLowerCase();
  const transitionLevel = riskTrendKey === "stable" ? "state" : riskTrendKey;

  document.body.dataset.transitionLevel = transitionLevel;
  document.body.classList.remove("is-dashboard-transitioning");
  void document.body.offsetWidth;
  document.body.classList.add("is-dashboard-transitioning");
  window.setTimeout(() => document.body.classList.remove("is-dashboard-transitioning"), 760);

  document.querySelectorAll(".system-status-row").forEach((row) => {
    row.classList.remove("is-runtime-active");
    void row.offsetWidth;
    row.classList.add("is-runtime-active");
    window.setTimeout(() => row.classList.remove("is-runtime-active"), 760);
  });

  const stateTargets = [
    ".driver-panel",
    ".mode-panel",
    ".system-status-panel",
  ];

  stateTargets.forEach((selector) => {
    const node = document.querySelector(selector);
    if (!node) return;

    node.dataset.reactionState = stateKey || "wachsam";
    node.classList.remove("is-state-panel-shift");
    void node.offsetWidth;
    node.classList.add("is-state-panel-shift");
    window.setTimeout(() => node.classList.remove("is-state-panel-shift"), 760);
  });

  pulseDataflowActivity([
    ".driver-panel",
    ".driver-readout",
    ".telemetry-panel",
    ".system-status-panel",
    ".event-timeline-panel",
  ], "is-driver-sync", 720);
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}

function setBar(id, value) {
  const node = document.getElementById(id);
  if (node) node.style.width = `${sanitizePercent(value)}%`;
}

function setMetric(valueId, barId, value) {
  const safeValue = sanitizePercent(value);
  setText(valueId, `${safeValue}%`);
  setBar(barId, safeValue);
}

function setRuntimeStatusRow(id, label, level) {
  setText(id, label);

  const row = document.getElementById(id)?.closest(".system-status-row");
  if (row) row.dataset.statusLevel = level;
}

function formatRuntimeSyncTime(date = new Date()) {
  return date.toLocaleTimeString("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  }[char]));
}

function renderEventTimeline() {
  const timeline = document.getElementById("event-timeline");
  if (!timeline) return;

  timeline.innerHTML = runtimeEvents.slice(0, 3).map((event) => `
    <div class="event-timeline__item" data-event-type="${escapeHtml(event.type)}">
      <span class="event-timeline__time">${escapeHtml(event.time)}</span>
      <strong>${escapeHtml(event.label)}</strong>
      <p>${escapeHtml(event.detail)}</p>
    </div>
  `).join("");

  const latestItem = timeline.querySelector(".event-timeline__item");
  if (latestItem) {
    latestItem.classList.add("is-event-new");
    window.setTimeout(() => latestItem.classList.remove("is-event-new"), 760);
  }
}

function pushRuntimeEvent(type, label, detail) {
  const nextEvent = {
    type,
    label,
    detail,
    time: formatRuntimeSyncTime(),
  };
  const previous = runtimeEvents[0];

  if (previous && previous.type === nextEvent.type && previous.label === nextEvent.label && previous.detail === nextEvent.detail) {
    previous.time = nextEvent.time;
  } else {
    runtimeEvents = [nextEvent, ...runtimeEvents].slice(0, 5);
  }

  renderEventTimeline();
}

function renderRuntimeStatus(dataset, derivedState, coupling = {}) {
  const backendOnline = backendRuntimeState === "online";
  const homeAssistantOnline = Boolean(dataset?.context?.homeAssistantConnected)
    || dataset?.context?.timeSource === "home_assistant";
  const driverEngineActive = Boolean(derivedState?.state);
  const mqttStatus = mqttRuntimeState === "published"
    ? { label: "MQTT Live", level: "ok" }
    : mqttRuntimeState === "prepared"
      ? { label: "MQTT Prepared", level: "warn" }
      : { label: "MQTT Simulated", level: "warn" };

  setRuntimeStatusRow("runtime-backend-status", backendOnline ? "Backend Online" : "Backend Offline", backendOnline ? "ok" : "error");
  setRuntimeStatusRow(
    "runtime-ha-status",
    coupling.homeAssistantStatus || (homeAssistantOnline ? "HA Sync: Connected" : "HA Standby"),
    coupling.homeAssistantLevel || (homeAssistantOnline ? "ok" : "warn"),
  );
  setRuntimeStatusRow("runtime-mqtt-status", coupling.mqttStatus || mqttStatus.label, mqttStatus.level);
  setRuntimeStatusRow("runtime-driver-engine-status", driverEngineActive ? "Engine Active" : "Engine Degraded", driverEngineActive ? "ok" : "error");
  setRuntimeStatusRow("runtime-last-sync", formatRuntimeSyncTime(), backendOnline ? "ok" : "warn");
}

function updateDebugOverlay({
  driverState,
  riskIndex,
  drivingMode,
  homeAssistantConnected,
  mqttTopic,
  lastEventTime,
} = {}) {
  setText("debug-driver-state", driverState || "-");
  setText("debug-risk-index", riskIndex ?? "-");
  setText("debug-driving-mode", drivingMode || "-");
  if (typeof homeAssistantConnected === "boolean") {
    setText("debug-ha-status", homeAssistantConnected ? "HA Sync" : "HA Standby");
  }
  setText("debug-mqtt-topic", mqttTopic || document.getElementById("mqtt-topic")?.textContent || "-");
  setText("debug-last-event-time", lastEventTime || lastDebugEventTime || "-");
}

function renderMqttEventBus(driverState, drivingMode, riskIndex, event = {}) {
  const payload = event.payload || {
    driverState,
    drivingMode,
    riskIndex,
    timestamp: new Date().toISOString(),
  };
  lastDebugEventTime = payload.timestamp
    ? formatRuntimeSyncTime(new Date(payload.timestamp))
    : formatRuntimeSyncTime();

  setText("mqtt-status", event.status || "MQTT Simulated");
  setText("mqtt-topic", event.topic || "porsche/driver/state");
  setText("mqtt-last-event", payload.driverState || driverState);
  setText("mqtt-payload", JSON.stringify(payload, null, 2));
  pushRuntimeEvent(
    "mqtt",
    "MQTT Event",
    `${event.topic || "porsche/driver/state"} / ${payload.driverState || driverState} / Risk ${payload.riskIndex ?? riskIndex}`,
  );
  updateDebugOverlay({
    driverState: payload.driverState || driverState,
    riskIndex: payload.riskIndex ?? riskIndex,
    drivingMode: payload.drivingMode || drivingMode,
    mqttTopic: event.topic || "porsche/driver/state",
    lastEventTime: lastDebugEventTime,
  });

  const mqttPanel = document.querySelector(".mqtt-panel");
  if (mqttPanel) {
    const mqttStatus = String(event.status || "");
    mqttRuntimeState = mqttStatus ? (mqttStatus.includes("Published") ? "published" : "prepared") : "simulated";
    mqttPanel.dataset.mqttState = mqttRuntimeState;
    const runtimeMqttStatus = mqttRuntimeState === "published"
      ? { label: "MQTT Live", level: "ok" }
      : mqttRuntimeState === "prepared"
        ? { label: event.status || "MQTT Prepared", level: "warn" }
        : { label: "MQTT Simulated", level: "warn" };
    setRuntimeStatusRow("runtime-mqtt-status", runtimeMqttStatus.label, runtimeMqttStatus.level);
    setRuntimeStatusRow("runtime-last-sync", formatRuntimeSyncTime(), "ok");
    pulseDataflowActivity([
      ".mqtt-panel",
      ".system-status-panel",
      ".telemetry-panel",
      ".event-timeline-panel",
    ], "is-dataflow-sync", 680);
    mqttPanel.classList.remove("is-mqtt-updated");
    void mqttPanel.offsetWidth;
    mqttPanel.classList.add("is-mqtt-updated");
    const mqttRows = mqttPanel.querySelectorAll(".telemetry-row");
    mqttRows.forEach((row) => {
      row.classList.remove("is-row-updated");
      void row.offsetWidth;
      row.classList.add("is-row-updated");
      window.setTimeout(() => row.classList.remove("is-row-updated"), 760);
    });
    window.setTimeout(() => mqttPanel.classList.remove("is-mqtt-updated"), 900);
  }
}

function applyBackendMqttEvent(mqttEvent) {
  if (!mqttEvent?.payload) return;

  const statusLabel = mqttEvent.sent
    ? "MQTT Live: Published"
    : mqttEvent.lastError
      ? "MQTT Prepared: Not sent"
      : "MQTT Prepared";

  renderMqttEventBus(
    mqttEvent.payload.driverState,
    mqttEvent.payload.drivingMode,
    mqttEvent.payload.riskIndex,
    {
      payload: mqttEvent.payload,
      topic: mqttEvent.topic,
      status: statusLabel,
    },
  );

  if (mqttEvent.lastError) {
    pushRuntimeEvent("mqtt", "MQTT Prepared", mqttEvent.lastError);
  }
}

function applyBackendTriggerStatus(result) {
  const haStatus = result?.homeAssistantStatus;
  const mqttStatus = result?.mqttStatus;

  if (haStatus) {
    const isHaOk = Boolean(haStatus.ok);
    const label = isHaOk
      ? "HA Trigger: Sent"
      : haStatus.status === "not_configured"
        ? "HA Not Configured"
        : haStatus.status === "timeout"
          ? "HA Timeout"
          : "HA Unreachable";
    setRuntimeStatusRow("runtime-ha-status", label, isHaOk ? "ok" : "error");
    if (haStatus.lastError) {
      pushRuntimeEvent("ha", "HA Error", haStatus.lastError);
    }
  }

  if (mqttStatus) {
    const isMqttOk = Boolean(mqttStatus.sent);
    setRuntimeStatusRow(
      "runtime-mqtt-status",
      isMqttOk ? "MQTT Live" : "MQTT Prepared",
      isMqttOk ? "ok" : "warn",
    );
  }
}

async function refreshBackendMqttEvent() {
  const response = await fetch(MQTT_LAST_EVENT_ENDPOINT, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) return;

  const result = await response.json();
  applyBackendMqttEvent(result.mqtt);
}

function triggerSystemReactionActivity(driverState, riskTrendKey) {
  const stateKey = String(driverState || "").trim().toLowerCase();
  const reactionTargets = [
    ".mqtt-panel",
    ".context-panel",
    ".intelligence-panel",
    ".warning-panel",
    ".driver-readout",
    ".system-status-panel",
    ".telemetry-panel",
    ".mode-panel",
  ];

  reactionTargets.forEach((selector) => {
    const node = document.querySelector(selector);
    if (!node) return;

    node.dataset.reactionState = stateKey || "wachsam";
    node.dataset.riskTrend = riskTrendKey || "stable";
    node.classList.remove("is-system-reacting");
    void node.offsetWidth;
    node.classList.add("is-system-reacting");
    window.setTimeout(() => node.classList.remove("is-system-reacting"), 920);
  });
}

function triggerHomeAssistantAction(drivingMode, driverState, riskIndex, coupling = {}) {
  const riskBand = Math.floor(sanitizePercent(riskIndex) / 10) * 10;
  const triggerKey = [
    String(driverState || "-").trim().toLowerCase(),
    riskBand,
    coupling.eventPriority || "-",
  ].join("|");

  if (!lastHomeAssistantTriggerKey) {
    lastHomeAssistantTriggerKey = triggerKey;
    return;
  }

  if (triggerKey === lastHomeAssistantTriggerKey) return;
  lastHomeAssistantTriggerKey = triggerKey;
  pushRuntimeEvent(
    "ha",
    "HA Trigger",
    `${coupling.homeAssistantStatus || "Home Assistant"} / ${driverState} / Risk ${riskIndex}`,
  );
  pulseDataflowActivity([
    "#external-source-chip",
    "#smart-context-status",
    ".context-panel",
    ".system-status-panel",
    ".event-timeline-panel",
  ], "is-ha-sync", 720);

  fetch(HOME_ASSISTANT_TRIGGER_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      drivingMode,
      driverState,
      riskIndex,
      supportStrategy: coupling.strategy,
      triggerReason: coupling.triggerReason,
      eventPriority: coupling.eventPriority,
      syncMode: coupling.syncMode,
    }),
  }).then(async (response) => {
    if (response.ok) {
      const result = await response.json();
      applyBackendTriggerStatus(result);
      applyBackendMqttEvent(result.mqtt);
      return;
    }

    await refreshBackendMqttEvent();
  }).catch((error) => {
    console.info("Home Assistant trigger failed:", error.message);
    refreshBackendMqttEvent().catch((refreshError) => {
      console.info("MQTT event refresh failed:", refreshError.message);
    });
  });
}

function isVisibleRiskFactor(label) {
  const normalizedLabel = String(label || "").toLowerCase();
  return !normalizedLabel.includes("ablenkung") && !normalizedLabel.includes("abgelenkt");
}

function getVisibleRiskFormula(formulaText) {
  return String(formulaText || "-")
    .replace(/\s*\+\s*Ablenkung\s*[+-]?\d+/i, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function getVisibleRiskDetails(detailsText) {
  return String(detailsText || "")
    .split("|")
    .map((part) => part.trim())
    .filter(isVisibleRiskFactor)
    .join(" | ");
}

function readDisplayedPercent(elementId, fallbackValue) {
  const node = document.getElementById(elementId);
  const parsedValue = Number.parseInt(String(node?.textContent || "").replace(/[^\d.-]/g, ""), 10);
  return sanitizePercent(Number.isFinite(parsedValue) ? parsedValue : fallbackValue);
}

function readDisplayedRisk(fallbackValue) {
  return readDisplayedPercent("risk-score", fallbackValue);
}

function easeSystemStateProgress(progress) {
  const t = Math.max(0, Math.min(1, progress));
  return t * t * t * (t * (t * 6 - 15) + 10);
}

function interpolateValue(startValue, targetValue, progress) {
  return Math.round(startValue + (targetValue - startValue) * progress);
}

function cancelStateValueAnimation() {
  if (stateValueAnimation.frameId) {
    window.cancelAnimationFrame(stateValueAnimation.frameId);
  }

  if (stateValueAnimation.completionTimer) {
    window.clearTimeout(stateValueAnimation.completionTimer);
  }

  stateValueAnimation = {
    frameId: null,
    completionTimer: null,
  };
  document.body.classList.remove("is-state-value-animating");
}

function animateStateValuesToTarget(targetDataset) {
  const targetStress = sanitizePercent(targetDataset.telemetry?.stress);
  const targetEnergy = sanitizePercent(targetDataset.telemetry?.energy);
  const targetFocus = sanitizePercent(targetDataset.telemetry?.focus);
  const targetRiskContext = calculateNightAdjustedRisk(targetDataset.assessment?.riskScore, false);
  targetRiskContext.weatherImpact = Number(targetDataset.assessment?.weatherImpact || 0);
  const targetRisk = sanitizePercent(targetRiskContext.finalRisk);
  const startValues = {
    stress: readDisplayedPercent("stress-value", targetStress),
    energy: readDisplayedPercent("energy-value", targetEnergy),
    focus: readDisplayedPercent("focus-value", targetFocus),
    risk: readDisplayedRisk(targetRisk),
  };
  const startTime = performance.now();

  cancelStateValueAnimation();
  document.body.classList.add("is-state-value-animating");

  function renderFrame(timestamp) {
    const elapsed = timestamp - startTime;
    const progress = easeSystemStateProgress(Math.min(elapsed / STATE_VALUE_ANIMATION_DURATION, 1));
    const displayedStress = interpolateValue(startValues.stress, targetStress, progress);
    const displayedEnergy = interpolateValue(startValues.energy, targetEnergy, progress);
    const displayedFocus = interpolateValue(startValues.focus, targetFocus, progress);
    const displayedRisk = interpolateValue(startValues.risk, targetRisk, progress);
    const displayedState = deriveDriverStateFromRisk(displayedRisk);

    setMetric("stress-value", "stress-bar", displayedStress);
    setMetric("energy-value", "energy-bar", displayedEnergy);
    setMetric("focus-value", "focus-bar", displayedFocus);
    applyRiskMeter(displayedRisk, displayedState.theme);
    setModeMarker(displayedRisk);

    if (progress < 1) {
      stateValueAnimation.frameId = window.requestAnimationFrame(renderFrame);
      return;
    }

    stateValueAnimation.frameId = null;
    stateValueAnimation.completionTimer = window.setTimeout(() => {
      stateValueAnimation.completionTimer = null;
      document.body.classList.remove("is-state-value-animating");
      renderDashboard(targetDataset);
    }, 90);
  }

  stateValueAnimation.frameId = window.requestAnimationFrame(renderFrame);
}

function setModeMarker(riskScore) {
  const markerTrack = document.querySelector(".mode-marker");
  const marker = document.getElementById("mode-marker");
  if (!marker) return;

  const { markerPosition, mode } = deriveDrivingModePresentation(riskScore);
  const trackWidth = markerTrack?.clientWidth || 0;
  const markerWidth = marker.offsetWidth || 18;
  const travelWidth = Math.max(0, trackWidth - markerWidth);
  const markerX = trackWidth > 0
    ? (travelWidth * markerPosition) / 100
    : 0;

  marker.style.setProperty("--mode-marker-x", `${markerX}px`);
  if (markerTrack) {
    markerTrack.dataset.drivingMode = String(mode || "").trim().toLowerCase();
  }
}

function applyTheme(theme) {
  const heroPanel = document.querySelector(".driver-panel");
  const topbar = document.querySelector(".topbar");
  const tagRow = document.querySelector(".intelligence-panel");

  ["theme-green", "theme-yellow", "theme-orange", "theme-red"].forEach((className) => {
    heroPanel?.classList.remove(className);
    topbar?.classList.remove(className);
    tagRow?.classList.remove(className);
  });

  heroPanel?.classList.add(`theme-${theme}`);
  topbar?.classList.add(`theme-${theme}`);
  tagRow?.classList.add(`theme-${theme}`);
}

function applyRiskMeter(score, theme) {
  const safeScore = sanitizePercent(score);
  const meter = document.getElementById("risk-meter");
  const colorMap = {
    green: "#5ef2a1",
    yellow: "#ffb84d",
    orange: "#ff7a29",
    red: "#ff4d6d",
  };
  const channelMap = {
    green: "94 242 161",
    yellow: "255 184 77",
    orange: "255 122 41",
    red: "255 77 109",
  };
  const stateMap = {
    green: "alert",
    yellow: "tired",
    orange: "tired",
    red: "critical",
  };
  const resolvedTheme = colorMap[theme] ? theme : "orange";
  const [r, g, b] = channelMap[resolvedTheme].split(" ");

  if (meter) {
    meter.style.setProperty("--value", safeScore);
    meter.style.setProperty("--risk-color", colorMap[resolvedTheme]);
    meter.style.setProperty("--risk-rgb", `${r} ${g} ${b}`);
    meter.dataset.riskState = stateMap[resolvedTheme] || "tired";
  }
  setText("risk-score", safeScore);
}

function deriveRiskTrend(currentRisk, previousRisk) {
  const safeCurrentRisk = sanitizePercent(currentRisk);
  const safePreviousRisk = Number.isFinite(previousRisk) ? sanitizePercent(previousRisk) : null;

  if (safePreviousRisk === null || safeCurrentRisk === safePreviousRisk) {
    return {
      key: "stable",
      label: "Stable",
      analysis: "Risk Trend: stable -> Lage weiter beobachten",
    };
  }

  if (safeCurrentRisk > safePreviousRisk) {
    return {
      key: "rising",
      label: "Rising Risk",
      analysis: "Risk Trend: rising -> Aufmerksamkeit erhoehen",
    };
  }

  return {
    key: "decreasing",
    label: "Decreasing Risk",
    analysis: "Risk Trend: decreasing -> Belastung sinkt",
  };
}

function applyRiskTrendDisplay(riskTrend) {
  const badge = document.getElementById("risk-trend-badge");
  if (!badge) return;

  badge.dataset.riskTrend = riskTrend.key;
  setText("risk-trend-badge", riskTrend.label);
}

function calculateNightAdjustedRisk(baseRisk, isNight) {
  const safeBaseRisk = sanitizePercent(baseRisk);
  const nightModifier = isNight ? 10 : 0;
  const finalRisk = sanitizePercent(safeBaseRisk + nightModifier);

  return {
    baseRisk: safeBaseRisk,
    nightModifier,
    finalRisk,
  };
}

function applyRiskInfluenceDisplay(riskContext) {
  const influence = document.getElementById("risk-influence");
  if (!influence) return;

  const parts = [];

  if (riskContext.sensorModifier > 0) {
    parts.push(`Sensor Impact +${riskContext.sensorModifier} Risk`);
  }

  if (riskContext.weatherImpact > 0) {
    parts.push(`Weather Impact +${riskContext.weatherImpact} Risk`);
  }

  if (riskContext.nightModifier > 0) {
    parts.push(`Night Influence +${riskContext.nightModifier}`);
  }

  influence.textContent = parts.join(" | ");
  influence.hidden = parts.length === 0;
}

function randomInt(min, max) {
  return Math.round(min + Math.random() * (max - min));
}

function randomFromRange([min, max]) {
  return sanitizePercent(randomInt(min, max));
}

function chooseDemoProfile(profiles) {
  const extremeAlertProfile = profiles.find((profile) => profile.key === "extrem wachsam");
  if (extremeAlertProfile && Math.random() < 0.2) {
    return extremeAlertProfile;
  }

  const standardProfiles = profiles.filter((profile) => profile.key !== "extrem wachsam");
  return standardProfiles[randomInt(0, standardProfiles.length - 1)];
}

function injectExtremeMetric(metrics, profileKey) {
  if (Math.random() >= 0.2) return metrics;

  const metricNames = ["stress", "energy", "focus"];
  const metricName = metricNames[randomInt(0, metricNames.length - 1)];
  const isAlertProfile = profileKey === "wachsam" || profileKey === "extrem wachsam";
  const prefersHighExtreme = metricName === "stress" ? profileKey === "kritisch" : isAlertProfile;
  const extremeRange = prefersHighExtreme ? [90, 100] : [0, 10];

  return {
    ...metrics,
    [metricName]: randomFromRange(extremeRange),
  };
}

function resolveTimeContext(dataset) {
  const derivedContext = deriveDayNightContext(dataset?.time?.clock);
  const context = dataset?.context || {};

  if (typeof context.isNight !== "boolean") {
    return derivedContext;
  }

  return {
    ...derivedContext,
    isNight: context.isNight,
    timeOfDay: context.timeOfDay || (context.isNight ? "Night" : "Day"),
    modeLabel: context.isNight ? "NIGHT MODE ACTIVE" : "DAY MODE",
    phaseLabel: context.isNight ? "Night Operation" : "Day Operation",
    influenceLabel: context.isNight
      ? "Night Influence +10 due to reduced visibility and higher fatigue sensitivity."
      : "Day Influence +0 with standard visibility baseline.",
  };
}

function getTimeSourceLabel(timeSource) {
  if (timeSource === "home_assistant") return "Home Assistant";
  if (timeSource === "system_time") return "System Time";
  return "Scenario Time";
}

function isTooSimilarToPrevious(metrics, previousMetrics) {
  return ["stress", "energy", "focus"].every(
    (metricName) => Math.abs(metrics[metricName] - previousMetrics[metricName]) < 8,
  );
}

function calculateBaselineRisk(stress, energy, focus, criticalManeuver, weather, isNight, randomOffset) {
  const stressComponent = Number((stress * 0.45).toFixed(1));
  const energyComponent = Number(((100 - energy) * 0.35).toFixed(1));
  const focusComponent = Number(((100 - focus) * 0.2).toFixed(1));
  const distraction = deriveDistractionState(focus);
  const maneuverState = deriveCriticalManeuverState(criticalManeuver);
  const offset = Math.max(-5, Math.min(5, Number.isFinite(randomOffset) ? Number(randomOffset) : randomInt(-5, 5)));
  const nightModifier = deriveNightRiskModifier(isNight, energy, focus);
  const weatherImpact = deriveWeatherRiskModifier(weather, stress, focus);

  const baselineRisk = sanitizePercent(
    Math.round(
      stressComponent
      + energyComponent
      + focusComponent
      + distraction.riskModifier
      + nightModifier
      + maneuverState.riskModifier
      + offset
      + weatherImpact,
    ),
  );

  return {
    baselineRisk,
    stressComponent,
    energyComponent,
    focusComponent,
    distraction,
    maneuverState,
    offset,
    nightModifier,
    weatherImpact,
  };
}

function calculateProfileRisk(stress, energy, focus, heartRate, drivingContext, criticalManeuver, isNight, weather, randomOffset) {
  const baseline = calculateBaselineRisk(
    stress,
    energy,
    focus,
    criticalManeuver,
    weather,
    isNight,
    randomOffset,
  );
  const baselineState = deriveDriverStateFromRisk(baseline.baselineRisk, {
    stress,
    energy,
    focus,
    isNight,
    weather,
  });
  const parsedHeartRate = Number(heartRate);
  const consistentHeartRate = Number.isFinite(parsedHeartRate)
    ? sanitizeHeartRate(parsedHeartRate)
    : deriveSimulatedHeartRate({
      stress,
      riskScore: baseline.baselineRisk,
      driverState: baselineState.state,
    });
  const heartRateSensor = deriveHeartRateSensorState(consistentHeartRate);
  const awarenessBoost = deriveAwarenessBoostState(heartRateSensor.state, baseline.maneuverState.key);

  const baseRisk = sanitizePercent(
    Math.round(
      baseline.stressComponent
      + baseline.energyComponent
      + baseline.focusComponent
      + baseline.distraction.riskModifier
      + baseline.nightModifier
      + heartRateSensor.riskModifier
      + baseline.maneuverState.riskModifier
      + awarenessBoost.riskModifier
      + baseline.offset
      + baseline.weatherImpact,
    ),
  );

  return {
    baseRisk,
    baselineRisk: baseline.baselineRisk,
    randomOffset: baseline.offset,
    stressComponent: baseline.stressComponent,
    energyComponent: baseline.energyComponent,
    focusComponent: baseline.focusComponent,
    distractionState: baseline.distraction.state,
    distractionModifier: baseline.distraction.riskModifier,
    heartRate: heartRateSensor.bpm,
    heartRateState: heartRateSensor.state,
    heartRateUiState: heartRateSensor.uiState,
    heartRateStatusLabel: heartRateSensor.statusLabel,
    heartRateAnalysis: heartRateSensor.analysisLabel,
    heartRateImpactLabel: heartRateSensor.impactLabel,
    sensorModifier: heartRateSensor.riskModifier,
    criticalManeuver: baseline.maneuverState.key,
    criticalManeuverLabel: baseline.maneuverState.label,
    criticalManeuverImpact: baseline.maneuverState.riskModifier,
    criticalManeuverAnalysis: baseline.maneuverState.analysisLabel,
    criticalManeuverStrategy: baseline.maneuverState.strategyText,
    awarenessBoostImpact: awarenessBoost.riskModifier,
    awarenessBoostAnalysis: awarenessBoost.analysisLabel,
    awarenessBoostLabel: awarenessBoost.label,
    nightModifier: baseline.nightModifier,
    weatherImpact: baseline.weatherImpact,
    formulaText: `Stress ${baseline.stressComponent.toFixed(1)} + Energy ${baseline.energyComponent.toFixed(1)} + Focus ${baseline.focusComponent.toFixed(1)} + Ablenkung ${baseline.distraction.riskModifier >= 0 ? "+" : ""}${baseline.distraction.riskModifier} + Nacht ${baseline.nightModifier >= 0 ? "+" : ""}${baseline.nightModifier} + Wetter ${baseline.weatherImpact >= 0 ? "+" : ""}${baseline.weatherImpact} + Herzfrequenz ${heartRateSensor.riskModifier >= 0 ? "+" : ""}${heartRateSensor.riskModifier}${baseline.maneuverState.riskModifier > 0 ? ` + Manoever ${baseline.maneuverState.riskModifier}` : ""}${awarenessBoost.riskModifier > 0 ? ` + Kopplung ${awarenessBoost.riskModifier}` : ""} + Zufall ${baseline.offset >= 0 ? "+" : ""}${baseline.offset}`,
  };
}

function buildRiskExplanation(stress, energy, focus, drivingContext, isNight, weather, riskInputs) {
  const contributions = [];
  const drivers = [];
  const stabilizers = [];
  const contextLabel = String(drivingContext || "").trim();
  const normalizedContext = contextLabel.toLowerCase();
  const weatherLabel = String(weather || "").toLowerCase();
  const distractionState = riskInputs?.distractionState || deriveDistractionState(focus).state;
  const distractionModifier = Number(riskInputs?.distractionModifier || 0);
  const heartRateState = riskInputs?.heartRateState || "normal";
  const sensorModifier = Number(riskInputs?.sensorModifier || 0);
  const maneuverLabel = riskInputs?.criticalManeuverLabel || "Kein kritisches Manoever";
  const maneuverImpact = Number(riskInputs?.criticalManeuverImpact || 0);
  const awarenessBoostLabel = riskInputs?.awarenessBoostLabel || "";
  const awarenessBoostImpact = Number(riskInputs?.awarenessBoostImpact || 0);

  if (isNight) {
    contributions.push({
      label: "Nachtfahrt",
      value: deriveNightRiskModifier(isNight, energy, focus),
      type: "risk",
    });
  } else {
    contributions.push({ label: "Tagkontext", value: -1, type: "stabilizer" });
  }

  if (normalizedContext.includes("stadt")) {
    contributions.push({ label: "Stadtverkehr", value: stress < 60 ? 3 : 6, type: "risk" });
  } else if (normalizedContext.includes("autobahn")) {
    contributions.push({ label: "Autobahn", value: 2, type: "risk" });
  } else if (normalizedContext.includes("nacht")) {
    contributions.push({
      label: "Nachtfahrt-Kontext",
      value: energy >= 55 && focus >= 55 ? 3 : 4,
      type: "risk",
    });
  } else if (normalizedContext.includes("feierabend")) {
    contributions.push({ label: "Feierabendfahrt", value: energy >= 45 ? 3 : 7, type: "risk" });
  }

  if (isNight) {
    drivers.push("Nachtfahrt");
  } else {
    stabilizers.push("Tagkontext");
  }

  if (weatherLabel.includes("sturm")) {
    drivers.push("Sturm");
    contributions.push({ label: "Sturm", value: deriveWeatherRiskModifier(weather, stress, focus), type: "risk" });
  } else if (weatherLabel.includes("nebel")) {
    drivers.push("Nebel");
    contributions.push({ label: "Nebel", value: deriveWeatherRiskModifier(weather, stress, focus), type: "risk" });
  } else if (weatherLabel.includes("regen")) {
    drivers.push("Regen");
    contributions.push({ label: "Regen", value: deriveWeatherRiskModifier(weather, stress, focus), type: "risk" });
  } else if (weatherLabel.includes("wind")) {
    drivers.push("Wind");
    contributions.push({ label: "Wind", value: deriveWeatherRiskModifier(weather, stress, focus), type: "risk" });
  }

  if (stress >= 75) {
    drivers.push("hoher Stress");
    contributions.push({ label: "Stress", value: Math.max(1, Math.round((stress - 75) * 0.15)), type: "risk" });
  } else if (stress <= 20) {
    stabilizers.push("niedriger Stress");
    contributions.push({ label: "Stress", value: -Math.max(1, Math.round((20 - stress) * 0.08)), type: "stabilizer" });
  }

  if (energy <= 35) {
    drivers.push("niedrige Energy");
    contributions.push({ label: "Energy", value: Math.max(1, Math.round((35 - energy) * 0.09)), type: "risk" });
  } else if (energy >= 85) {
    stabilizers.push("hohe Energy");
    contributions.push({ label: "Energy", value: -Math.max(1, Math.round((energy - 85) * 0.08)), type: "stabilizer" });
  }

  if (focus <= 35) {
    drivers.push("niedriger Focus");
    contributions.push({ label: "Focus", value: Math.max(1, Math.round((35 - focus) * 0.08)), type: "risk" });
  } else if (focus >= 85) {
    stabilizers.push("hoher Focus");
    contributions.push({ label: "Focus", value: -Math.max(1, Math.round((focus - 85) * 0.07)), type: "stabilizer" });
  }

  if (distractionModifier > 0) {
    drivers.push(distractionState);
    contributions.push({
      label: `Ablenkung (${distractionState})`,
      value: distractionModifier,
      type: "risk",
    });
  }

  if (sensorModifier > 0) {
    drivers.push(`Herzfrequenz ${heartRateState}`);
    contributions.push({
      label: `Herzfrequenz (${heartRateState})`,
      value: sensorModifier,
      type: "risk",
    });
  }

  if (maneuverImpact > 0) {
    drivers.push(maneuverLabel);
    contributions.push({
      label: `Kritisches Manoever (${maneuverLabel})`,
      value: maneuverImpact,
      type: "risk",
    });
  }

  if (awarenessBoostImpact > 0) {
    drivers.push("Kombinationsbelastung");
    contributions.push({
      label: awarenessBoostLabel || "Awareness Boost",
      value: awarenessBoostImpact,
      type: "risk",
    });
  }

  if (drivers.length > 0) {
    const joinedDrivers = drivers.slice(0, 3).join(" + ");
    const summary = `${joinedDrivers} ${drivers.length === 1 ? "erhoeht" : "erhoehen"} das Risiko.`;
    const topDrivers = contributions
      .filter((item) => item.value > 0)
      .sort((left, right) => right.value - left.value)
      .slice(0, 3)
      .map((item) => item.label);
    const detailText = contributions
      .filter((item) => item.value !== 0)
      .sort((left, right) => Math.abs(right.value) - Math.abs(left.value))
      .slice(0, 4)
      .map((item) => `${item.label} ${item.value >= 0 ? "+" : ""}${item.value}`)
      .join(" | ");

    return { summary, topDrivers, contributions, detailText };
  }

  const joinedStabilizers = (stabilizers.length > 0 ? stabilizers : ["Ausgeglichene Werte"])
    .slice(0, 3)
    .join(" + ");
  return {
    summary: `${joinedStabilizers} ${joinedStabilizers.includes(" + ") ? "stabilisieren" : "stabilisiert"} den Zustand.`,
    topDrivers: contributions
      .filter((item) => item.value > 0)
      .sort((left, right) => right.value - left.value)
      .slice(0, 3)
      .map((item) => item.label),
    contributions,
    detailText: contributions
      .filter((item) => item.value !== 0)
      .sort((left, right) => Math.abs(right.value) - Math.abs(left.value))
      .slice(0, 4)
      .map((item) => `${item.label} ${item.value >= 0 ? "+" : ""}${item.value}`)
      .join(" | "),
  };
}

function recomputeAssessmentFromContext(dataset) {
  const nextDataset = structuredClone(dataset);
  const telemetry = nextDataset.telemetry || {};
  const context = nextDataset.context || {};
  const timeContext = resolveTimeContext(nextDataset);
  const stress = sanitizePercent(telemetry.stress ?? FALLBACK_DATA.telemetry.stress);
  const energy = sanitizePercent(telemetry.energy ?? FALLBACK_DATA.telemetry.energy);
  const focus = sanitizePercent(telemetry.focus ?? FALLBACK_DATA.telemetry.focus);
  const heartRate = deriveConsistentHeartRate(
    telemetry.heartRate ?? FALLBACK_DATA.telemetry.heartRate,
    nextDataset.assessment?.riskScore ?? FALLBACK_DATA.assessment.riskScore,
    nextDataset.assessment?.driverState ?? FALLBACK_DATA.assessment.driverState,
  );
  const riskInputs = calculateProfileRisk(
    stress,
    energy,
    focus,
    heartRate,
    context.drivingContext,
    context.criticalManeuver,
    timeContext.isNight,
    context.weather,
    nextDataset.assessment?.riskRandomOffset,
    context.homeAssistantConnected,
  );
  const finalRisk = riskInputs.baseRisk;
  const riskExplanation = buildRiskExplanation(
    stress,
    energy,
    focus,
    context.drivingContext,
    timeContext.isNight,
    context.weather,
    riskInputs,
  );
  const derivedState = deriveDriverStateFromRisk(finalRisk, {
    stress,
    energy,
    focus,
    heartRateState: riskInputs.heartRateState,
    isNight: timeContext.isNight,
    weather: context.weather,
  });
  const systemMode = deriveSystemModeFromDriverState(derivedState.state);
  const assistNarrative = deriveAssistReactionFromState(derivedState.state, focus, riskInputs);
  const mode = deriveDrivingModeFromRisk(finalRisk);
  let recommendation = "Gute Werte erkannt. Adaptive Unterstuetzung ruhig und stabil weiterfuehren.";
  const maneuverStrategy = riskInputs.criticalManeuverStrategy;

  if (derivedState.warningLevel === "ROT") {
    recommendation = "Assistenz deutlich erhoehen und zeitnah Pause oder Fahrerwechsel empfehlen.";
  } else if (derivedState.warningLevel === "ORANGE") {
    recommendation = timeContext.isNight
      ? "Home Assistant meldet Nachtkontext. Aufmerksamkeit stabilisieren und fruehe Pause empfehlen."
      : "Kontextdaten zeigen mittlere Belastung. Aufmerksamkeit aktiv halten und Reizdichte niedrig fuehren.";
  }

  if (maneuverStrategy) {
    recommendation = `${recommendation} ${maneuverStrategy}.`;
  }

  nextDataset.time = {
    ...nextDataset.time,
    phase: timeContext.phaseLabel,
  };
  nextDataset.context = {
    ...context,
    timeOfDay: timeContext.timeOfDay,
    isNight: timeContext.isNight,
    criticalManeuver: context.criticalManeuver || "none",
  };
  nextDataset.telemetry = {
    ...telemetry,
    heartRate: riskInputs.heartRate,
    inputSummary: context.homeAssistantConnected
      ? "Context adaptation active / HA Sync"
      : telemetry.inputSummary || FALLBACK_DATA.telemetry.inputSummary,
  };
  nextDataset.assessment = {
    ...nextDataset.assessment,
    driverState: derivedState.state,
    systemMode: systemMode.label,
    systemModeKey: systemMode.key,
    mode,
    riskScore: riskInputs.baseRisk,
    riskFormula: riskInputs.formulaText,
    distractionState: riskInputs.distractionState,
    distractionModifier: riskInputs.distractionModifier,
    heartRateState: riskInputs.heartRateState,
    heartRateUiState: riskInputs.heartRateUiState,
    heartRateStatusLabel: riskInputs.heartRateStatusLabel,
    heartRateAnalysis: riskInputs.heartRateAnalysis,
    heartRateImpactLabel: riskInputs.heartRateImpactLabel,
    sensorModifier: riskInputs.sensorModifier,
    criticalManeuverState: riskInputs.criticalManeuver,
    criticalManeuverLabel: riskInputs.criticalManeuverLabel,
    criticalManeuverImpact: riskInputs.criticalManeuverImpact,
    criticalManeuverAnalysis: riskInputs.criticalManeuverAnalysis,
    criticalManeuverStrategy: riskInputs.criticalManeuverStrategy,
    awarenessBoostImpact: riskInputs.awarenessBoostImpact,
    awarenessBoostAnalysis: riskInputs.awarenessBoostAnalysis,
    awarenessBoostLabel: riskInputs.awarenessBoostLabel,
    riskRandomOffset: riskInputs.randomOffset,
    nightModifier: riskInputs.nightModifier,
    weatherImpact: riskInputs.weatherImpact,
    warningLevel: derivedState.warningLevel,
    recommendation,
    reason: riskExplanation.summary,
    riskDrivers: riskExplanation.topDrivers,
    riskContributions: riskExplanation.contributions,
    riskDetails: riskExplanation.detailText,
    assistReaction: assistNarrative.assistReaction,
    lightMode: timeContext.isNight ? "Aktivierungslicht" : "Komfortlicht",
    aiSummary: context.homeAssistantConnected
      ? `Home Assistant erweitert Wetter-, Tageszeit- und Zustandskontext fuer die Assistenzlogik.${maneuverStrategy ? ` ${maneuverStrategy}.` : ""}`
      : `${maneuverStrategy ? `Kritisches Fahrmanoever aktiv. ${maneuverStrategy}.` : "Kontext beeinflusst Bewertung und Empfehlung."}`,
    warningPriority: derivedState.warningLevel === "ROT" ? "High" : derivedState.warningLevel === "ORANGE" ? "Medium" : "Low",
    warningTrigger: context.homeAssistantConnected
      ? `Home Assistant sync: ${context.weather || "Context updated"}`
      : timeContext.isNight ? "Night influence active" : "Day context baseline",
    warningAction: recommendation,
  };

  return nextDataset;
}

function buildSimulatedHomeAssistantContext(dataset) {
  const baseClock = dataset?.time?.clock;
  const fallbackNow = new Date();
  const simulatedClock = typeof baseClock === "string" && /^\d{2}:\d{2}$/.test(baseClock)
    ? baseClock
    : `${String(fallbackNow.getHours()).padStart(2, "0")}:${String(fallbackNow.getMinutes()).padStart(2, "0")}`;
  const timeContext = deriveDayNightContext(simulatedClock);
  const weather = timeContext.isNight ? "Regen" : "Klar";

  return {
    clock: simulatedClock,
    time_of_day: timeContext.timeOfDay,
    is_night: timeContext.isNight,
    weather,
    driving_context: timeContext.isNight ? "Nachtfahrt" : "Stadtverkehr",
    critical_maneuver: "none",
    home_assistant: timeContext.isNight
      ? "Home status synced: Aussenbeleuchtung aktiv, Morgenroutine inaktiv"
      : "Home status synced: Morgenroutine aktiv, Haus im Tagesmodus",
    weather_sensor: weather === "Regen" ? "Rain probability elevated" : "Clear visibility baseline",
    traffic: timeContext.isNight ? "Gering" : "Moderat",
    status: "HA Sync: Connected",
  };
}

function normalizeHomeAssistantContext(payload, dataset) {
  const source = payload || {};
  const fallbackClock = dataset?.time?.clock || FALLBACK_DATA.time.clock;
  const clock = source.clock || source.uhrzeit || fallbackClock;
  const derivedTime = deriveDayNightContext(clock);
  const explicitIsNight = typeof source.is_night === "boolean" ? source.is_night : undefined;
  const isNight = explicitIsNight ?? derivedTime.isNight;
  const timeOfDay = source.time_of_day || source.timeOfDay || (isNight ? "Night" : "Day");
  const weather = source.weather || source.wetter || dataset?.context?.weather || FALLBACK_DATA.context.weather;
  const detailParts = [
    source.home_assistant,
    source.kalenderstatus,
    source.geraetestatus,
    source.hinweis,
  ].filter(Boolean);

  return {
    clock,
    timeOfDay,
    isNight,
    weather,
    drivingContext: source.driving_context || source.fahrkontext || dataset?.context?.drivingContext || FALLBACK_DATA.context.drivingContext,
    criticalManeuver: source.critical_maneuver || source.criticalManeuver || dataset?.context?.criticalManeuver || FALLBACK_DATA.context.criticalManeuver,
    homeAssistant: detailParts.join(" | ") || "HA context synced",
    weatherSensor: source.weather_sensor || (String(weather).toLowerCase().includes("regen") ? "Rain probability elevated" : "Context weather stable"),
    traffic: source.traffic || dataset?.context?.traffic || FALLBACK_DATA.context.traffic,
    connectionStatus: source.status || "HA Sync: Connected",
    smartContextStatus: "Smart Context: HA Sync",
  };
}

async function loadHomeAssistantContext(dataset) {
  try {
    const response = await fetch(HOME_ASSISTANT_ENDPOINT, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Home Assistant antwortete mit ${response.status}`);
    }

    const payload = await response.json();
    return normalizeHomeAssistantContext(payload, dataset);
  } catch (error) {
    console.info("Fallback auf simulierte Home-Assistant-Daten:", error.message);
    return normalizeHomeAssistantContext(buildSimulatedHomeAssistantContext(dataset), dataset);
  }
}

function applyHomeAssistantContext(dataset, homeAssistantContext) {
  const nextDataset = structuredClone(dataset);

  nextDataset.system = {
    ...nextDataset.system,
    systemLabel: homeAssistantContext.connectionStatus || "HA Sync: Connected",
  };
  nextDataset.time = {
    ...nextDataset.time,
    clock: homeAssistantContext.clock || nextDataset.time?.clock,
  };
  nextDataset.context = {
    ...nextDataset.context,
    drivingContext: homeAssistantContext.drivingContext || nextDataset.context?.drivingContext,
    criticalManeuver: homeAssistantContext.criticalManeuver || nextDataset.context?.criticalManeuver || "none",
    weather: homeAssistantContext.weather || nextDataset.context?.weather,
    timeOfDay: homeAssistantContext.timeOfDay || nextDataset.context?.timeOfDay,
    isNight: typeof homeAssistantContext.isNight === "boolean"
      ? homeAssistantContext.isNight
      : nextDataset.context?.isNight,
    timeSource: "home_assistant",
    homeAssistantConnected: true,
    smartContextStatus: homeAssistantContext.smartContextStatus || "Smart Context: HA Sync",
    homeAssistant: homeAssistantContext.homeAssistant || nextDataset.context?.homeAssistant,
    weatherSensor: homeAssistantContext.weatherSensor || nextDataset.context?.weatherSensor,
    traffic: homeAssistantContext.traffic || nextDataset.context?.traffic,
  };

  return recomputeAssessmentFromContext(nextDataset);
}

function removeHomeAssistantContext(dataset) {
  const nextDataset = structuredClone(dataset || FALLBACK_DATA);

  nextDataset.system = {
    ...nextDataset.system,
    systemLabel: "System Online",
  };
  nextDataset.context = {
    ...nextDataset.context,
    timeSource: "system_time",
    homeAssistantConnected: false,
    smartContextStatus: "Smart Context: Local Sync",
    homeAssistant: "No HA data",
  };

  return recomputeAssessmentFromContext(nextDataset);
}

function simulateAssessmentUpdate(dataset) {
  const nextDataset = structuredClone(dataset);
  const telemetry = nextDataset.telemetry || {};
  const context = nextDataset.context || {};
  const timeContext = deriveDayNightContext(nextDataset.time?.clock);
  const profiles = [
    {
      key: "extrem wachsam",
      stress: [0, 5],
      energy: [95, 100],
      focus: [95, 100],
    },
    {
      key: "wachsam",
      stress: [0, 10],
      energy: [90, 100],
      focus: [90, 100],
    },
    {
      key: "muede",
      stress: [30, 65],
      energy: [30, 65],
      focus: [30, 65],
    },
    {
      key: "kritisch",
      stress: [75, 100],
      energy: [0, 25],
      focus: [0, 25],
    },
  ];
  const previousMetrics = {
    stress: sanitizePercent(telemetry.stress ?? FALLBACK_DATA.telemetry.stress),
    energy: sanitizePercent(telemetry.energy ?? FALLBACK_DATA.telemetry.energy),
    focus: sanitizePercent(telemetry.focus ?? FALLBACK_DATA.telemetry.focus),
  };
  let selectedProfile = profiles[0];
  let nextMetrics = previousMetrics;

  for (let attempt = 0; attempt < 12; attempt += 1) {
    selectedProfile = chooseDemoProfile(profiles);
    nextMetrics = injectExtremeMetric({
      stress: randomFromRange(selectedProfile.stress),
      energy: randomFromRange(selectedProfile.energy),
      focus: randomFromRange(selectedProfile.focus),
    }, selectedProfile.key);

    if (!isTooSimilarToPrevious(nextMetrics, previousMetrics)) {
      break;
    }
  }

  if (isTooSimilarToPrevious(nextMetrics, previousMetrics)) {
    const fallbackProfile =
      previousMetrics.stress >= 65 || previousMetrics.energy <= 35 || previousMetrics.focus <= 35
        ? profiles.find((profile) => profile.key === "wachsam")
        : profiles.find((profile) => profile.key === "kritisch");

    selectedProfile = fallbackProfile || profiles[1];
    nextMetrics = injectExtremeMetric({
      stress: randomFromRange(selectedProfile.stress),
      energy: randomFromRange(selectedProfile.energy),
      focus: randomFromRange(selectedProfile.focus),
    }, selectedProfile.key);
  }

  const { stress, energy, focus } = nextMetrics;
  telemetry.stress = stress;
  telemetry.energy = energy;
  telemetry.focus = focus;

  const riskInputs = calculateProfileRisk(
    stress,
    energy,
    focus,
    undefined,
    context.drivingContext,
    context.criticalManeuver,
    timeContext.isNight,
    context.weather,
    undefined,
    context.homeAssistantConnected,
  );
  const baseRisk = riskInputs.baseRisk;
  telemetry.heartRate = riskInputs.heartRate;
  const riskContext = {
    baseRisk,
    nightModifier: riskInputs.nightModifier,
    sensorModifier: riskInputs.sensorModifier,
    weatherImpact: riskInputs.weatherImpact,
    finalRisk: baseRisk,
  };
  const riskExplanation = buildRiskExplanation(
    stress,
    energy,
    focus,
    context.drivingContext,
    timeContext.isNight,
    context.weather,
    riskInputs,
  );
  const derivedState = deriveDriverStateFromRisk(riskContext.finalRisk, {
    stress,
    energy,
    focus,
    heartRateState: riskInputs.heartRateState,
    isNight: timeContext.isNight,
    weather: context.weather,
    riskTrend: deriveRiskTrend(riskContext.finalRisk, previousRenderedRiskScore).key,
  });
  const systemMode = deriveSystemModeFromDriverState(derivedState.state);
  const assistNarrative = deriveAssistReactionFromState(derivedState.state, focus, riskInputs);
  const mode = deriveDrivingModeFromRisk(riskContext.finalRisk);
  let recommendation = "Gute Werte erkannt. Adaptive Unterstuetzung ruhig und stabil weiterfuehren.";
  const maneuverStrategy = riskInputs.criticalManeuverStrategy;

  if (derivedState.warningLevel === "ROT") {
    recommendation = "Assistenz deutlich erhoehen und zeitnah Pause oder Fahrerwechsel empfehlen.";
  } else if (derivedState.warningLevel === "ORANGE") {
    recommendation = timeContext.isNight
      ? "Nachtkontext aktiv: Aufmerksamkeit stabilisieren und fruehe Pause empfehlen."
      : "Mittlere Belastung erkannt. Aufmerksamkeit aktiv halten und Reizdichte niedrig fuehren.";
  }

  if (maneuverStrategy) {
    recommendation = `${recommendation} ${maneuverStrategy}.`;
  }

  nextDataset.assessment = {
    ...nextDataset.assessment,
    driverState: derivedState.state,
    systemMode: systemMode.label,
    systemModeKey: systemMode.key,
    mode,
    riskScore: baseRisk,
    riskFormula: riskInputs.formulaText,
    distractionState: riskInputs.distractionState,
    distractionModifier: riskInputs.distractionModifier,
    heartRateState: riskInputs.heartRateState,
    heartRateUiState: riskInputs.heartRateUiState,
    heartRateStatusLabel: riskInputs.heartRateStatusLabel,
    heartRateAnalysis: riskInputs.heartRateAnalysis,
    heartRateImpactLabel: riskInputs.heartRateImpactLabel,
    sensorModifier: riskInputs.sensorModifier,
    criticalManeuverState: riskInputs.criticalManeuver,
    criticalManeuverLabel: riskInputs.criticalManeuverLabel,
    criticalManeuverImpact: riskInputs.criticalManeuverImpact,
    criticalManeuverAnalysis: riskInputs.criticalManeuverAnalysis,
    criticalManeuverStrategy: riskInputs.criticalManeuverStrategy,
    awarenessBoostImpact: riskInputs.awarenessBoostImpact,
    awarenessBoostAnalysis: riskInputs.awarenessBoostAnalysis,
    awarenessBoostLabel: riskInputs.awarenessBoostLabel,
    riskRandomOffset: riskInputs.randomOffset,
    nightModifier: riskInputs.nightModifier,
    weatherImpact: riskInputs.weatherImpact,
    warningLevel: derivedState.warningLevel,
    recommendation,
    reason: riskExplanation.summary,
    riskDrivers: riskExplanation.topDrivers,
    riskContributions: riskExplanation.contributions,
    riskDetails: riskExplanation.detailText,
    assistReaction: assistNarrative.assistReaction,
    aiSummary: maneuverStrategy
      ? `Kontext beeinflusst Bewertung, Bewertung steuert ${mode.toLowerCase()} und Empfehlung. ${maneuverStrategy}.`
      : `Kontext beeinflusst Bewertung, Bewertung steuert ${mode.toLowerCase()} und Empfehlung.`,
    warningPriority: derivedState.warningLevel === "ROT" ? "High" : derivedState.warningLevel === "ORANGE" ? "Medium" : "Low",
    warningTrigger: timeContext.isNight ? "Night influence active" : "Day context baseline",
    warningAction: recommendation,
  };

  nextDataset.telemetry = telemetry;
  return nextDataset;
}

function updateScenarioStatus(isOverrideActive) {
  const liveChip = document.getElementById("live-chip");
  const simulationPanel = document.querySelector(".simulation-panel");
  const overrideBadge = document.getElementById("override-badge");
  if (!liveChip) return;

  liveChip.classList.toggle("is-live", !isOverrideActive);
  liveChip.classList.toggle("is-override", isOverrideActive);
  liveChip.textContent = isOverrideActive ? "Simulation Override" : "Runtime Sync";
  simulationPanel?.classList.toggle("is-override", isOverrideActive);
  if (overrideBadge) {
    overrideBadge.classList.toggle("is-simulation", isOverrideActive);
    overrideBadge.textContent = isOverrideActive ? "Simulation Override" : "Runtime Standard";
  }
}

function applyScenarioOverride(dataset, overrideValues) {
  const nextDataset = structuredClone(dataset);
  const nextTime = overrideValues.time || nextDataset.time?.clock || FALLBACK_DATA.time.clock;
  const nextContext = overrideValues.context || nextDataset.context?.drivingContext || FALLBACK_DATA.context.drivingContext;
  const nextCriticalManeuver = overrideValues.criticalManeuver || nextDataset.context?.criticalManeuver || FALLBACK_DATA.context.criticalManeuver;
  const nextWeather = overrideValues.weather || nextDataset.context?.weather || FALLBACK_DATA.context.weather;
  const timeContext = deriveDayNightContext(nextTime);

  nextDataset.system = {
    ...nextDataset.system,
    overrideMode: true,
  };
  nextDataset.time = {
    ...nextDataset.time,
    clock: nextTime,
    phase: timeContext.phaseLabel,
  };
  nextDataset.context = {
    ...nextDataset.context,
    drivingContext: nextContext,
    criticalManeuver: nextCriticalManeuver,
    weather: nextWeather,
    isNight: timeContext.isNight,
    timeOfDay: timeContext.timeOfDay,
    timeSource: "scenario_override",
  };
  nextDataset.telemetry = {
    ...nextDataset.telemetry,
    inputSummary: `Scenario Override active: ${nextContext} / ${nextWeather} / ${nextCriticalManeuver} / ${nextTime}`,
  };

  return recomputeAssessmentFromContext(nextDataset);
}

function getScenarioOverrideValues() {
  return {
    time: document.getElementById("sim-time")?.value || "",
    context: document.getElementById("sim-context")?.value || "",
    criticalManeuver: document.getElementById("sim-critical-maneuver")?.value || "none",
    weather: document.getElementById("sim-weather")?.value || "",
  };
}

function syncScenarioInputs(dataset) {
  const source = dataset || FALLBACK_DATA;
  const timeInput = document.getElementById("sim-time");
  const contextInput = document.getElementById("sim-context");
  const criticalManeuverInput = document.getElementById("sim-critical-maneuver");
  const weatherInput = document.getElementById("sim-weather");

  if (timeInput && source.time?.clock) timeInput.value = source.time.clock;
  if (contextInput && source.context?.drivingContext) contextInput.value = source.context.drivingContext;
  if (criticalManeuverInput && source.context?.criticalManeuver) criticalManeuverInput.value = source.context.criticalManeuver;
  if (weatherInput && source.context?.weather) weatherInput.value = source.context.weather;
}

function setupScenarioInteraction() {
  const button = document.getElementById("recalculate-state");
  const form = document.getElementById("simulation-form");
  const overrideInput = document.getElementById("sim-override");
  const resetButton = document.getElementById("reset-simulation");
  if (!button || !form || !overrideInput || !resetButton) return;

  button.addEventListener("click", () => {
    const sourceDataset = overrideInput.checked
      ? simulateAssessmentUpdate(
        applyScenarioOverride(
          baseSystemDataset || currentDataset || FALLBACK_DATA,
          getScenarioOverrideValues(),
        ),
      )
      : simulateAssessmentUpdate(baseSystemDataset || currentDataset || FALLBACK_DATA);

    currentDataset = sourceDataset;
    animateStateValuesToTarget(currentDataset);
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!overrideInput.checked) {
      renderDashboard(baseSystemDataset || currentDataset || FALLBACK_DATA);
      updateScenarioStatus(false);
      return;
    }

    currentDataset = applyScenarioOverride(
      baseSystemDataset || currentDataset || FALLBACK_DATA,
      getScenarioOverrideValues(),
    );
    renderDashboard(currentDataset);
    updateScenarioStatus(true);
  });

  overrideInput.addEventListener("change", () => {
    const isOverrideActive = overrideInput.checked;
    updateScenarioStatus(isOverrideActive);

    if (isOverrideActive) {
      if (!document.getElementById("sim-time")?.value) {
        syncScenarioInputs(currentDataset || baseSystemDataset || FALLBACK_DATA);
      }
      return;
    }

    currentDataset = structuredClone(baseSystemDataset || FALLBACK_DATA);
    renderDashboard(currentDataset);
  });

  resetButton.addEventListener("click", () => {
    overrideInput.checked = false;
    updateScenarioStatus(false);
    syncScenarioInputs(baseSystemDataset || FALLBACK_DATA);
    currentDataset = structuredClone(baseSystemDataset || FALLBACK_DATA);
    renderDashboard(currentDataset);
  });
}

function projectScanPoint(x, y, z, rotationY, canvas) {
  const centeredX = x - 50;
  const centeredY = y - 50;
  const centeredZ = z - 50;
  const cosY = Math.cos(rotationY);
  const sinY = Math.sin(rotationY);
  const rotatedX = centeredX * cosY - centeredZ * sinY;
  const rotatedZ = centeredX * sinY + centeredZ * cosY;
  const scale = 2.15;
  const depth = 380 / (380 + rotatedZ);

  return {
    x: canvas.width * 0.4 + rotatedX * scale * depth,
    y: canvas.height * 0.7 - centeredY * scale * depth,
    depth,
  };
}

function drawScanAxis(ctx, canvas, rotationY, axis, color, label) {
  const origin = projectScanPoint(0, 0, 0, rotationY, canvas);
  const target = projectScanPoint(axis.x, axis.y, axis.z, rotationY, canvas);

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(origin.x, origin.y);
  ctx.lineTo(target.x, target.y);
  ctx.stroke();

  ctx.fillStyle = color;
  ctx.font = '600 15px "Rajdhani", sans-serif';
  ctx.fillText(label, target.x + 8, target.y - 6);
}

function drawScanGrid(ctx, canvas, rotationY) {
  ctx.strokeStyle = "rgba(140, 166, 199, 0.18)";
  ctx.lineWidth = 1;

  for (let step = 0; step <= 100; step += 25) {
    const start = projectScanPoint(step, 0, 0, rotationY, canvas);
    const end = projectScanPoint(step, 0, 100, rotationY, canvas);
    const rise = projectScanPoint(step, 100, 0, rotationY, canvas);

    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(rise.x, rise.y);
    ctx.stroke();
  }

  for (let step = 0; step <= 100; step += 25) {
    const start = projectScanPoint(0, step, 0, rotationY, canvas);
    const end = projectScanPoint(100, step, 0, rotationY, canvas);
    const depth = projectScanPoint(0, step, 100, rotationY, canvas);

    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(depth.x, depth.y);
    ctx.stroke();
  }
}

function setupHomeAssistantIntegration() {
  const connectButton = document.getElementById("connect-home-assistant");
  const disconnectButton = document.getElementById("disconnect-home-assistant");
  if (!connectButton) return;

  connectButton.addEventListener("click", async () => {
    const sourceDataset = structuredClone(currentDataset || baseSystemDataset || FALLBACK_DATA);

    connectButton.disabled = true;
    connectButton.textContent = "Connecting HA Sync...";

    try {
      const homeAssistantContext = await loadHomeAssistantContext(sourceDataset);
      const nextDataset = applyHomeAssistantContext(sourceDataset, homeAssistantContext);

      if (!document.getElementById("sim-override")?.checked) {
        baseSystemDataset = structuredClone(nextDataset);
      }

      currentDataset = nextDataset;
      renderDashboard(nextDataset);
      syncScenarioInputs(nextDataset);
    } finally {
      connectButton.textContent = "Connect HA Sync";
      renderHomeAssistantControls();
    }
  });

  if (disconnectButton) {
    disconnectButton.addEventListener("click", () => {
      const sourceDataset = structuredClone(currentDataset || baseSystemDataset || FALLBACK_DATA);
      const nextDataset = removeHomeAssistantContext(sourceDataset);

      if (!document.getElementById("sim-override")?.checked) {
        baseSystemDataset = structuredClone(nextDataset);
      }

      currentDataset = nextDataset;
      renderDashboard(nextDataset);
      syncScenarioInputs(nextDataset);
    });
  }
}

function renderHomeAssistantControls() {
  const isConnected = Boolean(currentDataset?.context?.homeAssistantConnected)
    || currentDataset?.context?.timeSource === "home_assistant";
  const connectButton = document.getElementById("connect-home-assistant");
  const disconnectButton = document.getElementById("disconnect-home-assistant");

  if (connectButton) {
    connectButton.classList.toggle("is-connected", isConnected);
    connectButton.disabled = isConnected;
  }

  if (disconnectButton) {
    disconnectButton.classList.toggle("is-connected", isConnected);
    disconnectButton.disabled = !isConnected;
  }
}

function drawScanFace(ctx, points, fillColor, strokeColor, lineWidth) {
  ctx.fillStyle = fillColor;
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = lineWidth;
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  points.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

function resolveScanColor(template, alpha) {
  return template.replace("__ALPHA__", `${alpha}`);
}

function getScanZoneGeometry(bounds, rotationY, canvas) {
  const [x0, x1] = bounds.x;
  const [y0, y1] = bounds.y;
  const [z0, z1] = bounds.z;

  return {
    frontBottomLeft: projectScanPoint(x0, y0, z1, rotationY, canvas),
    frontBottomRight: projectScanPoint(x1, y0, z1, rotationY, canvas),
    frontTopRight: projectScanPoint(x1, y1, z1, rotationY, canvas),
    frontTopLeft: projectScanPoint(x0, y1, z1, rotationY, canvas),
    backBottomLeft: projectScanPoint(x0, y0, z0, rotationY, canvas),
    backBottomRight: projectScanPoint(x1, y0, z0, rotationY, canvas),
    backTopRight: projectScanPoint(x1, y1, z0, rotationY, canvas),
    backTopLeft: projectScanPoint(x0, y1, z0, rotationY, canvas),
  };
}

function drawScanZone(ctx, canvas, rotationY, zoneConfig, isActive) {
  const geometry = getScanZoneGeometry(zoneConfig.bounds, rotationY, canvas);
  const {
    frontBottomLeft,
    frontBottomRight,
    frontTopRight,
    frontTopLeft,
    backBottomLeft,
    backBottomRight,
    backTopRight,
    backTopLeft,
  } = geometry;
  const fillAlpha = isActive ? 1 : 0.55;
  const edgeAlpha = isActive ? 1 : 0.68;

  drawScanFace(
    ctx,
    [backTopLeft, backTopRight, frontTopRight, frontTopLeft],
    resolveScanColor(zoneConfig.topFill, zoneConfig.topAlpha * fillAlpha),
    resolveScanColor(zoneConfig.edgeColor, edgeAlpha),
    isActive ? 1.5 : 1,
  );
  drawScanFace(
    ctx,
    [frontBottomRight, backBottomRight, backTopRight, frontTopRight],
    resolveScanColor(zoneConfig.sideFill, zoneConfig.sideAlpha * fillAlpha),
    resolveScanColor(zoneConfig.edgeColor, edgeAlpha),
    isActive ? 1.5 : 1,
  );
  drawScanFace(
    ctx,
    [frontBottomLeft, frontBottomRight, frontTopRight, frontTopLeft],
    resolveScanColor(zoneConfig.frontFill, zoneConfig.frontAlpha * fillAlpha),
    resolveScanColor(zoneConfig.edgeColor, edgeAlpha),
    isActive ? 1.6 : 1.1,
  );

  ctx.strokeStyle = resolveScanColor(zoneConfig.edgeColor, isActive ? 0.95 : 0.35);
  ctx.lineWidth = isActive ? 1.5 : 1;
  [
    [backBottomLeft, backBottomRight],
    [backBottomRight, backTopRight],
    [backTopRight, backTopLeft],
    [backTopLeft, backBottomLeft],
    [backBottomLeft, frontBottomLeft],
    [backBottomRight, frontBottomRight],
    [backTopLeft, frontTopLeft],
    [backTopRight, frontTopRight],
  ].forEach(([from, to]) => {
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
  });

  return projectScanPoint(
    zoneConfig.labelAnchor.x,
    zoneConfig.labelAnchor.y,
    zoneConfig.labelAnchor.z,
    rotationY,
    canvas,
  );
}

function drawScanZoneLayer(ctx, canvas, rotationY, zoneConfig, activeZone) {
  const isActive = zoneConfig.label === activeZone;
  const labelColor = isActive ? zoneConfig.activeLabel : zoneConfig.labelColor;

  if (isActive) {
    const center = projectScanPoint(
      (zoneConfig.bounds.x[0] + zoneConfig.bounds.x[1]) / 2,
      (zoneConfig.bounds.y[0] + zoneConfig.bounds.y[1]) / 2,
      (zoneConfig.bounds.z[0] + zoneConfig.bounds.z[1]) / 2,
      rotationY,
      canvas,
    );
    const glow = ctx.createRadialGradient(center.x, center.y, 10, center.x, center.y, 92);
    glow.addColorStop(0, zoneConfig.activeGlow);
    glow.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(center.x, center.y, 92, 0, Math.PI * 2);
    ctx.fill();
  }

  if (zoneConfig.ambientGlow) {
    const center = projectScanPoint(
      (zoneConfig.bounds.x[0] + zoneConfig.bounds.x[1]) / 2,
      (zoneConfig.bounds.y[0] + zoneConfig.bounds.y[1]) / 2,
      (zoneConfig.bounds.z[0] + zoneConfig.bounds.z[1]) / 2,
      rotationY,
      canvas,
    );
    const glow = ctx.createRadialGradient(center.x, center.y, 8, center.x, center.y, zoneConfig.ambientGlowRadius);
    glow.addColorStop(0, zoneConfig.ambientGlow);
    glow.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(center.x, center.y, zoneConfig.ambientGlowRadius, 0, Math.PI * 2);
    ctx.fill();
  }

  const labelPoint = drawScanZone(ctx, canvas, rotationY, zoneConfig, isActive);
  ctx.fillStyle = labelColor;
  ctx.font = isActive ? '700 15px "Orbitron", sans-serif' : '700 12px "Rajdhani", sans-serif';
  ctx.fillText(isActive ? `${zoneConfig.label} ACTIVE` : zoneConfig.label, labelPoint.x + 8, labelPoint.y - 6);
}

function mapValueToRange(value, targetRange) {
  const safeValue = sanitizePercent(value) / 100;
  return targetRange[0] + (targetRange[1] - targetRange[0]) * safeValue;
}

function resolveScanDisplayPosition(stress, energy, focus, zoneConfig) {
  return {
    x: mapValueToRange(stress, zoneConfig.pointBounds.x),
    y: mapValueToRange(energy, zoneConfig.pointBounds.y),
    z: mapValueToRange(focus, zoneConfig.pointBounds.z),
  };
}

function drawScanGuideLines(ctx, canvas, rotationY, stress, energy, focus, point) {
  const xPlane = projectScanPoint(stress, 0, focus, rotationY, canvas);
  const yPlane = projectScanPoint(0, energy, focus, rotationY, canvas);
  const zPlane = projectScanPoint(stress, energy, 0, rotationY, canvas);

  ctx.strokeStyle = "rgba(255, 220, 170, 0.42)";
  ctx.lineWidth = 1.4;
  ctx.setLineDash([7, 6]);

  ctx.beginPath();
  ctx.moveTo(point.x, point.y);
  ctx.lineTo(xPlane.x, xPlane.y);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(point.x, point.y);
  ctx.lineTo(yPlane.x, yPlane.y);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(point.x, point.y);
  ctx.lineTo(zPlane.x, zPlane.y);
  ctx.stroke();

  ctx.setLineDash([]);
}

function drawStatePoint(ctx, point, elapsed, palette) {
  const pulse = 0.5 + 0.5 * Math.sin(elapsed / 420);
  const haloRadius = 31 + pulse * 11;
  const outerHaloRadius = 53 + pulse * 15;

  const outerGlow = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, outerHaloRadius);
  outerGlow.addColorStop(0, palette.outerGlow);
  outerGlow.addColorStop(1, palette.outerGlowFade);
  ctx.fillStyle = outerGlow;
  ctx.beginPath();
  ctx.arc(point.x, point.y, outerHaloRadius, 0, Math.PI * 2);
  ctx.fill();

  const halo = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, haloRadius);
  halo.addColorStop(0, palette.innerCore);
  halo.addColorStop(0.32, palette.innerGlow);
  halo.addColorStop(1, palette.innerGlowFade);
  ctx.fillStyle = halo;
  ctx.beginPath();
  ctx.arc(point.x, point.y, haloRadius, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = palette.ringStroke.replace("__ALPHA__", `${0.45 + pulse * 0.28}`);
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  ctx.arc(point.x, point.y, 17.6 + pulse * 4.4, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = palette.centerFill;
  ctx.beginPath();
  ctx.arc(point.x, point.y, 10.45, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = palette.centerStroke;
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  ctx.arc(point.x, point.y, 14.85, 0, Math.PI * 2);
  ctx.stroke();
}

function deriveScanInterpretation(assessment) {
  const normalizedState = String(assessment?.driverState || "").trim().toLowerCase();
  const resolvedState = normalizedState || deriveDriverStateFromRisk(assessment?.riskScore).state.toLowerCase();

  if (resolvedState === "kritisch") {
    return {
      zone: "Critical Zone",
      headline: "Critical driver state",
      summary: "Der Zustand ist kritisch. Die Assistenz sollte direkt eingreifen und eine Pause oder einen Fahrerwechsel priorisieren.",
    };
  }

  if (resolvedState === "muede") {
    return {
      zone: "Watch Zone",
      headline: "Adaptive watch zone",
      summary: "Der Zustand ist beobachtbar, aber nicht kritisch. Die Assistenz sollte den Fahrer praesent begleiten und auf Veraenderungen reagieren.",
    };
  }

  return {
    zone: "Stable Zone",
    headline: "Stable driver state",
    summary: "Der Zustand ist stabil. Der Fahrer ist wachsam, die Assistenz bleibt ruhig und begleitet ohne zusaetzlichen Eingriff.",
  };
}

function renderStateScan() {
  const overlay = document.getElementById("scan-overlay");
  const canvas = document.getElementById("state-scan-canvas");
  if (!overlay || overlay.hidden || !canvas) return;

  const ctx = canvas.getContext("2d");
  const assessment = currentDataset?.assessment || FALLBACK_DATA.assessment;
  const telemetry = currentDataset?.telemetry || FALLBACK_DATA.telemetry;
  const stress = sanitizePercent(telemetry.stress);
  const energy = sanitizePercent(telemetry.energy);
  const focus = sanitizePercent(telemetry.focus);
  const interpretation = deriveScanInterpretation(assessment);
  const zoneKey = interpretation.zone.toLowerCase().replace(/\s+/g, "-");
  const zoneConfigs = [
    {
      label: "Stable Zone",
      bounds: { x: [8, 28], y: [72, 92], z: [70, 90] },
      pointBounds: { x: [10, 26], y: [75, 89], z: [73, 87] },
      labelAnchor: { x: 8, y: 94, z: 90 },
      frontFill: "rgba(94, 242, 161, __ALPHA__)",
      topFill: "rgba(94, 242, 161, __ALPHA__)",
      sideFill: "rgba(94, 242, 161, __ALPHA__)",
      frontAlpha: 0.07,
      topAlpha: 0.04,
      sideAlpha: 0.03,
      edgeColor: "rgba(94, 242, 161, __ALPHA__)",
      labelColor: "rgba(94, 242, 161, 0.42)",
      activeLabel: "rgba(214, 255, 232, 0.98)",
      activeGlow: "rgba(94, 242, 161, 0.24)",
    },
    {
      label: "Watch Zone",
      bounds: { x: [38, 62], y: [40, 64], z: [38, 62] },
      pointBounds: { x: [41, 59], y: [44, 60], z: [41, 59] },
      labelAnchor: { x: 38, y: 66, z: 62 },
      frontFill: "rgba(255, 184, 77, __ALPHA__)",
      topFill: "rgba(255, 184, 77, __ALPHA__)",
      sideFill: "rgba(255, 184, 77, __ALPHA__)",
      frontAlpha: 0.085,
      topAlpha: 0.05,
      sideAlpha: 0.04,
      edgeColor: "rgba(255, 184, 77, __ALPHA__)",
      labelColor: "rgba(255, 196, 102, 0.5)",
      activeLabel: "rgba(255, 240, 204, 0.98)",
      activeGlow: "rgba(255, 184, 77, 0.24)",
    },
    {
      label: "Critical Zone",
      bounds: { x: [72, 92], y: [10, 30], z: [10, 30] },
      pointBounds: { x: [75, 90], y: [12, 27], z: [12, 27] },
      labelAnchor: { x: 72, y: 32, z: 30 },
      frontFill: "rgba(255, 58, 92, __ALPHA__)",
      topFill: "rgba(255, 58, 92, __ALPHA__)",
      sideFill: "rgba(255, 58, 92, __ALPHA__)",
      frontAlpha: 0.09,
      topAlpha: 0.055,
      sideAlpha: 0.045,
      edgeColor: "rgba(255, 58, 92, __ALPHA__)",
      labelColor: "rgba(255, 88, 118, 0.52)",
      activeLabel: "rgba(255, 228, 234, 0.98)",
      activeGlow: "rgba(255, 58, 92, 0.28)",
      ambientGlow: "rgba(255, 58, 92, 0.12)",
      ambientGlowRadius: 62,
    },
  ];
  const activeZoneConfig = zoneConfigs.find((zoneConfig) => zoneConfig.label === interpretation.zone) || zoneConfigs[1];
  const displayPosition = resolveScanDisplayPosition(stress, energy, focus, activeZoneConfig);
  const pointPaletteByZone = {
    "stable-zone": {
      outerGlow: "rgba(94, 242, 161, 0.34)",
      outerGlowFade: "rgba(94, 242, 161, 0)",
      innerCore: "rgba(218, 255, 232, 0.96)",
      innerGlow: "rgba(94, 242, 161, 0.56)",
      innerGlowFade: "rgba(94, 242, 161, 0)",
      ringStroke: "rgba(222, 255, 234, __ALPHA__)",
      centerFill: "#eefdf3",
      centerStroke: "#ffffff",
    },
    "watch-zone": {
      outerGlow: "rgba(255, 184, 77, 0.34)",
      outerGlowFade: "rgba(255, 184, 77, 0)",
      innerCore: "rgba(255, 214, 122, 0.96)",
      innerGlow: "rgba(255, 184, 77, 0.56)",
      innerGlowFade: "rgba(255, 184, 77, 0)",
      ringStroke: "rgba(255, 236, 196, __ALPHA__)",
      centerFill: "#fff1cf",
      centerStroke: "#ffffff",
    },
    "critical-zone": {
      outerGlow: "rgba(255, 77, 109, 0.34)",
      outerGlowFade: "rgba(255, 77, 109, 0)",
      innerCore: "rgba(255, 210, 220, 0.96)",
      innerGlow: "rgba(255, 77, 109, 0.56)",
      innerGlowFade: "rgba(255, 77, 109, 0)",
      ringStroke: "rgba(255, 220, 228, __ALPHA__)",
      centerFill: "#ffe6eb",
      centerStroke: "#ffffff",
    },
  };
  const startedAt = performance.now();
  const scanModal = document.querySelector("#scan-overlay .scan-modal");

  setText("scan-stress", `${stress}`);
  setText("scan-energy", `${energy}`);
  setText("scan-focus", `${focus}`);
  setText("scan-position", `(${stress}, ${energy}, ${focus})`);
  setText("scan-position-hint", "Position = (Stress, Energy, Focus)");
  setText("scan-axis-explainer", "X = Stress, Y = Energy, Z = Focus. Hoehere Werte verschieben den Punkt entlang der jeweiligen Achse.");
  setText("scan-headline", interpretation.headline);
  setText("scan-summary", interpretation.summary);
  if (scanModal) {
    scanModal.dataset.activeZone = zoneKey;
  }

  const paint = (now) => {
    if (overlay.hidden) return;

    const elapsed = now - startedAt;
    const rotationY = -0.55 + Math.sin(elapsed / 1600) * 0.18;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "rgba(6, 10, 18, 0.96)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    zoneConfigs.forEach((zoneConfig) => drawScanZoneLayer(ctx, canvas, rotationY, zoneConfig, interpretation.zone));
    drawScanGrid(ctx, canvas, rotationY);
    drawScanAxis(ctx, canvas, rotationY, { x: 100, y: 0, z: 0 }, "#ff6a3d", "Stress");
    drawScanAxis(ctx, canvas, rotationY, { x: 0, y: 100, z: 0 }, "#5ef2a1", "Energy");
    drawScanAxis(ctx, canvas, rotationY, { x: 0, y: 0, z: 100 }, "#69e8ff", "Focus");

    const point = projectScanPoint(displayPosition.x, displayPosition.y, displayPosition.z, rotationY, canvas);
    drawScanGuideLines(ctx, canvas, rotationY, displayPosition.x, displayPosition.y, displayPosition.z, point);
    drawStatePoint(ctx, point, elapsed, pointPaletteByZone[zoneKey] || pointPaletteByZone["watch-zone"]);

    scanAnimationFrame = window.requestAnimationFrame(paint);
  };

  if (scanAnimationFrame) {
    window.cancelAnimationFrame(scanAnimationFrame);
  }
  scanAnimationFrame = window.requestAnimationFrame(paint);
}

function openStateScan() {
  const overlay = document.getElementById("scan-overlay");
  if (!overlay) return;
  overlay.hidden = false;
  renderStateScan();
}

function closeStateScan() {
  const overlay = document.getElementById("scan-overlay");
  if (!overlay) return;
  overlay.hidden = true;

  if (scanAnimationFrame) {
    window.cancelAnimationFrame(scanAnimationFrame);
    scanAnimationFrame = null;
  }
}

function setupStateScan() {
  const openButton = document.getElementById("open-state-scan");
  const closeButton = document.getElementById("close-state-scan");
  const backdrop = document.getElementById("scan-overlay-close");
  if (!openButton || !closeButton || !backdrop) return;

  openButton.addEventListener("click", openStateScan);
  closeButton.addEventListener("click", closeStateScan);
  backdrop.addEventListener("click", closeStateScan);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeStateScan();
  });
}

function applyDayNightFeature(timeContext, sourceLabel) {
  const feature = document.getElementById("day-night-feature");
  if (!feature) return;

  feature.classList.remove("is-day", "is-night");
  feature.classList.add(timeContext.isNight ? "is-night" : "is-day");

  setText("day-night-label", timeContext.modeLabel);
  setText("day-night-meta", `Derived from ${sourceLabel} ${timeContext.clock}`);
  setText("time-context-derivation", `${sourceLabel} ${timeContext.clock} -> ${timeContext.timeOfDay} mode derived`);
  setText("time-of-day-value", `${timeContext.timeOfDay} (derived from ${sourceLabel})`);
}

function normalizeDashboardPayload(data) {
  const dataset = structuredClone(data || FALLBACK_DATA);
  const telemetry = dataset.telemetry || {};
  const assessment = dataset.assessment || {};
  const rawRiskScore = sanitizePercent(
    assessment.riskScore ?? assessment.risk_score ?? FALLBACK_DATA.assessment.riskScore,
  );
  const normalizedHeartRate = deriveConsistentHeartRate(
    telemetry.heartRate ?? telemetry.heart_rate ?? FALLBACK_DATA.telemetry.heartRate,
    rawRiskScore,
    assessment.driverState ?? assessment.driver_state ?? FALLBACK_DATA.assessment.driverState,
  );
  const derivedHeartRate = deriveHeartRateSensorState(
    normalizedHeartRate,
  );
  const hasExplicitSensorModifier = assessment.sensorModifier != null || assessment.sensor_modifier != null;
  const normalizedRiskScore = hasExplicitSensorModifier
    ? rawRiskScore
    : sanitizePercent(rawRiskScore + derivedHeartRate.riskModifier);

  dataset.telemetry = {
    ...telemetry,
    heartRate: derivedHeartRate.bpm,
  };
  dataset.context = {
    ...(dataset.context || {}),
    criticalManeuver: dataset?.context?.criticalManeuver ?? dataset?.context?.critical_maneuver ?? FALLBACK_DATA.context.criticalManeuver,
  };
  dataset.assessment = {
    ...assessment,
    riskScore: normalizedRiskScore,
    heartRateState: assessment.heartRateState ?? assessment.heart_rate_state ?? derivedHeartRate.state,
    heartRateUiState: assessment.heartRateUiState ?? assessment.heart_rate_ui_state ?? derivedHeartRate.uiState,
    heartRateStatusLabel: assessment.heartRateStatusLabel ?? assessment.heart_rate_status_label ?? derivedHeartRate.statusLabel,
    heartRateAnalysis: assessment.heartRateAnalysis ?? assessment.heart_rate_analysis ?? derivedHeartRate.analysisLabel,
    heartRateImpactLabel: assessment.heartRateImpactLabel ?? assessment.heart_rate_impact_label ?? derivedHeartRate.impactLabel,
    sensorModifier: assessment.sensorModifier ?? assessment.sensor_modifier ?? derivedHeartRate.riskModifier,
    nightModifier: assessment.nightModifier ?? assessment.night_modifier ?? 0,
    weatherImpact: assessment.weatherImpact ?? assessment.weather_impact ?? 0,
    criticalManeuverState: assessment.criticalManeuverState ?? assessment.critical_maneuver_state ?? dataset.context.criticalManeuver,
    criticalManeuverLabel: assessment.criticalManeuverLabel ?? assessment.critical_maneuver_label ?? deriveCriticalManeuverState(dataset.context.criticalManeuver).label,
    criticalManeuverImpact: assessment.criticalManeuverImpact ?? assessment.critical_maneuver_impact ?? deriveCriticalManeuverState(dataset.context.criticalManeuver).riskModifier,
    criticalManeuverAnalysis: assessment.criticalManeuverAnalysis ?? assessment.critical_maneuver_analysis ?? deriveCriticalManeuverState(dataset.context.criticalManeuver).analysisLabel,
    criticalManeuverStrategy: assessment.criticalManeuverStrategy ?? assessment.critical_maneuver_strategy ?? deriveCriticalManeuverState(dataset.context.criticalManeuver).strategyText,
    awarenessBoostImpact: assessment.awarenessBoostImpact ?? assessment.awareness_boost_impact ?? deriveAwarenessBoostState(derivedHeartRate.state, dataset.context.criticalManeuver).riskModifier,
    awarenessBoostAnalysis: assessment.awarenessBoostAnalysis ?? assessment.awareness_boost_analysis ?? deriveAwarenessBoostState(derivedHeartRate.state, dataset.context.criticalManeuver).analysisLabel,
    awarenessBoostLabel: assessment.awarenessBoostLabel ?? assessment.awareness_boost_label ?? deriveAwarenessBoostState(derivedHeartRate.state, dataset.context.criticalManeuver).label,
  };

  return dataset;
}

function deriveHeartRateRiskDiscrepancy(riskScore, heartRateState) {
  const safeRiskScore = sanitizePercent(riskScore);
  const normalizedHeartRateState = String(heartRateState || "normal").trim().toLowerCase();

  if (normalizedHeartRateState === "kritisch erhoeht" && safeRiskScore < 35) {
    return "Ungewoehnliche Diskrepanz zwischen physiologischem Zustand und Risikobewertung.";
  }

  if (normalizedHeartRateState === "normal" && safeRiskScore >= 65) {
    return "Ungewoehnliche Diskrepanz zwischen physiologischem Zustand und Risikobewertung.";
  }

  return "";
}

function applyHeartRateSensorDisplay(dataset) {
  const heartRate = sanitizeHeartRate(dataset?.telemetry?.heartRate ?? FALLBACK_DATA.telemetry.heartRate);
  const derivedHeartRate = deriveHeartRateSensorState(heartRate);
  const uiState = derivedHeartRate.uiState;
  const statusLabel = derivedHeartRate.statusLabel;
  const impactLabel = dataset?.assessment?.heartRateImpactLabel || derivedHeartRate.impactLabel;
  const sensorModifier = Number(dataset?.assessment?.sensorModifier || 0);
  const discrepancyMessage = deriveHeartRateRiskDiscrepancy(
    dataset?.assessment?.riskScore ?? FALLBACK_DATA.assessment.riskScore,
    derivedHeartRate.state,
  );
  const gaugeValue = Math.round(((heartRate - 60) / 70) * 100);
  const heartRateCard = document.getElementById("heart-rate-card");
  const heartRateGauge = document.getElementById("heart-rate-gauge");
  const discrepancyNode = document.getElementById("heart-rate-discrepancy");

  setText("heart-rate-value", heartRate);
  setText("heart-rate-badge", statusLabel);
  setText("heart-rate-status", statusLabel);
  setText("heart-rate-impact", impactLabel);
  setText(
    "heart-rate-hint",
    sensorModifier > 0
      ? `Sensor input increases the Risk Index by ${sensorModifier} points.`
      : "Sensor input is currently within the normal prototype range and adds no extra Risk.",
  );
  if (discrepancyNode) {
    discrepancyNode.hidden = !discrepancyMessage;
    discrepancyNode.textContent = discrepancyMessage || "";
  }

  if (heartRateCard) {
    heartRateCard.dataset.sensorState = uiState;
  }

  if (heartRateGauge) {
    heartRateGauge.style.setProperty("--value", Math.max(0, Math.min(100, gaugeValue)));
  }
}

function renderDashboard(data) {
  const dataset = normalizeDashboardPayload(data || FALLBACK_DATA);
  const previousDriverState = document.body.dataset.driverState || "";
  const timeContext = resolveTimeContext(dataset);
  const sourceLabel = getTimeSourceLabel(dataset.context?.timeSource);
  const riskContext = calculateNightAdjustedRisk(dataset.assessment?.riskScore, false);
  const riskTrend = deriveRiskTrend(riskContext.finalRisk, previousRenderedRiskScore);
  riskContext.nightModifier = Number(dataset.assessment?.nightModifier || 0);
  riskContext.sensorModifier = Number(dataset.assessment?.sensorModifier || 0);
  riskContext.weatherImpact = Number(dataset.assessment?.weatherImpact || 0);
  const derivedState = deriveDriverStateFromRisk(riskContext.finalRisk, {
    stress: dataset.telemetry?.stress,
    energy: dataset.telemetry?.energy,
    focus: dataset.telemetry?.focus,
    heartRateState: dataset.assessment?.heartRateState,
    isNight: timeContext.isNight,
    weather: dataset.context?.weather,
    previousState: previousDriverState,
    riskTrend: riskTrend.key,
  });
  const systemMode = deriveSystemModeFromDriverState(derivedState.state);
  const systemDecision = deriveSystemDecisionFromDriverState(derivedState.state);
  const derivedDrivingMode = deriveDrivingModePresentation(riskContext.finalRisk);
  const normalizedDataset = {
    ...dataset,
    assessment: {
      ...dataset.assessment,
      driverState: derivedState.state,
      systemMode: dataset.assessment?.systemMode || systemMode.label,
      systemModeKey: dataset.assessment?.systemModeKey || systemMode.key,
      systemDecision: dataset.assessment?.systemDecision || systemDecision.text,
      systemDecisionKey: dataset.assessment?.systemDecisionKey || systemDecision.key,
      mode: derivedDrivingMode.mode,
      warningLevel: derivedState.warningLevel,
    },
  };
  let viewDataset = normalizedDataset;
  const coupling = deriveSystemCoupling(viewDataset, derivedState, riskContext, riskTrend);
  viewDataset = applySystemCouplingToDataset(viewDataset, coupling);
  currentDataset = structuredClone(viewDataset);
  const narrative = deriveNightAwareNarrative(viewDataset, timeContext);
  const systemDecisionReason = deriveSystemDecisionReason(viewDataset, derivedState, riskContext);
  const nextDriverState = String(derivedState.state || "").trim().toLowerCase();
  const isSystemReaction = Boolean(previousDriverState)
    && (previousDriverState !== nextDriverState || riskTrend.key !== "stable");
  document.body.dataset.driverState = nextDriverState;

  setText("system-status-label", viewDataset.system?.systemLabel || "System Online");
  setText("override-badge", viewDataset.system?.overrideMode ? "Simulation Override" : "Runtime Standard");
  const externalSourceConnected = Boolean(viewDataset.context?.homeAssistantConnected)
    || viewDataset.context?.timeSource === "home_assistant";
  setText("external-source-status", externalSourceConnected ? coupling.homeAssistantStatus : "HA Offline");
  const externalSourceChip = document.getElementById("external-source-chip");
  if (externalSourceChip) {
    externalSourceChip.dataset.sourceState = externalSourceConnected ? "connected" : "disconnected";
    externalSourceChip.dataset.supportLevel = coupling.supportLevel.toLowerCase();
  }
  setText("mental-state", derivedState.state);
  animateStateTransition("mental-state", derivedState.state);
  setText("system-decision-headline", viewDataset.assessment?.systemDecision || systemDecision.text);
  setText("system-decision-reason", systemDecisionReason);
  const systemDecisionNode = document.getElementById("system-decision");
  if (systemDecisionNode) {
    systemDecisionNode.dataset.decisionState = viewDataset.assessment?.systemDecisionKey || systemDecision.key;
  }
  animateStateTransition("system-decision", viewDataset.assessment?.systemDecisionKey || systemDecision.key);
  setText("system-mode-badge", viewDataset.assessment?.systemMode || systemMode.label);
  const systemModeBadge = document.getElementById("system-mode-badge");
  if (systemModeBadge) {
    systemModeBadge.dataset.systemMode = viewDataset.assessment?.systemModeKey || systemMode.key;
  }
  setText("warning-pill", derivedState.badge);
  animateStateTransition("warning-pill", derivedState.warningLevel);
  applyRiskTrendDisplay(riskTrend);
  setText("assist-reaction", narrative.assistReaction);
  const riskDriverText = (viewDataset.assessment?.riskDrivers || [])
    .filter(isVisibleRiskFactor)
    .slice(0, 3)
    .join(" | ");
  const riskDetailText = getVisibleRiskDetails(viewDataset.assessment?.riskDetails);
  const riskFormulaText = getVisibleRiskFormula(viewDataset.assessment?.riskFormula);
  setText(
    "reason-cause",
    [
      `${viewDataset.context?.drivingContext || "Kontext"} / ${viewDataset.context?.weather || "Wetter"}`,
      viewDataset.assessment?.criticalManeuverImpact > 0 ? `Manoever: ${viewDataset.assessment?.criticalManeuverLabel}` : "",
      riskDriverText,
      riskDetailText,
    ].filter(Boolean).join(" | "),
  );
  setText(
    "reason-analysis",
    [
      `Risk ${riskContext.finalRisk}`,
      riskTrend.analysis,
      derivedState.state,
      viewDataset.assessment?.heartRateAnalysis || "",
      viewDataset.assessment?.criticalManeuverAnalysis || "",
      viewDataset.assessment?.awarenessBoostAnalysis || "",
      riskFormulaText,
    ].filter(Boolean).join(" / "),
  );
  setText("reason-decision", `${coupling.drivingMode} / ${coupling.strategy}`);
  setText("driving-mode", coupling.drivingMode);
  setText("driving-mode-derivation", coupling.linkedSummary);
  setText("recommendation", `${viewDataset.assessment?.recommendation || narrative.recommendation} Strategy: ${coupling.strategy}.`);
  setText(
    "decision-input",
    `${viewDataset.context?.drivingContext || "Kontext"} / ${viewDataset.context?.weather || "Wetter"} / Manoever ${viewDataset.assessment?.criticalManeuverLabel || "Kein kritisches Manoever"} / Stress ${viewDataset.telemetry?.stress ?? "-"} / Energy ${viewDataset.telemetry?.energy ?? "-"} / Focus ${viewDataset.telemetry?.focus ?? "-"} / HR ${viewDataset.telemetry?.heartRate ?? "-"} bpm`,
  );
  setText(
    "decision-analysis",
    [
      `Risk ${riskContext.finalRisk}`,
      riskTrend.label,
      derivedState.state,
      coupling.supportLevel,
      coupling.syncMode,
      viewDataset.assessment?.criticalManeuverAnalysis || "",
      viewDataset.assessment?.heartRateAnalysis || "Heart Rate: No data",
      viewDataset.assessment?.awarenessBoostAnalysis || "",
    ].filter(Boolean).join(" / "),
  );
  setText(
    "decision-decision",
    `${coupling.drivingMode} / ${viewDataset.assessment?.systemMode || systemMode.label} / ${coupling.strategy}`,
  );
  setText(
    "decision-action",
    `${viewDataset.assessment?.recommendation || narrative.recommendation} Strategy: ${coupling.strategy}.`,
  );
  renderMqttEventBus(derivedState.state, coupling.drivingMode, riskContext.finalRisk, {
    topic: coupling.mqttTopic,
    status: coupling.mqttStatus,
    payload: {
      driverState: derivedState.state,
      drivingMode: coupling.drivingMode,
      riskIndex: riskContext.finalRisk,
      supportStrategy: coupling.strategy,
      triggerReason: coupling.triggerReason,
      supportLevel: coupling.supportLevel,
      homeAssistantStatus: coupling.homeAssistantStatus,
      eventPriority: coupling.eventPriority,
      syncMode: coupling.syncMode,
      riskTrend: riskTrend.key,
      timestamp: new Date().toISOString(),
    },
  });
  triggerHomeAssistantAction(coupling.drivingMode, derivedState.state, riskContext.finalRisk, coupling);
  renderRuntimeStatus(viewDataset, derivedState, coupling);
  updateDebugOverlay({
    driverState: derivedState.state,
    riskIndex: riskContext.finalRisk,
    drivingMode: coupling.drivingMode,
    homeAssistantConnected: externalSourceConnected,
    mqttTopic: coupling.mqttTopic,
    lastEventTime: lastDebugEventTime,
  });
  setText("context-label", `${viewDataset.context?.drivingContext || "Kontext"} / ${viewDataset.context?.weather || "Wetter"}`);
  setText("route-value", viewDataset.context?.route || "Unbekannt");
  setText("weather-value", viewDataset.context?.weather || "Unbekannt");
  setText("traffic-value", viewDataset.context?.traffic || "Unbekannt");
  setText(
    "home-assistant-value",
    externalSourceConnected
      ? `${viewDataset.context?.homeAssistant || "HA Connected"} / ${coupling.homeAssistantStatus}`
      : `${viewDataset.context?.homeAssistant || "No HA data"} / ${coupling.syncMode}`,
  );
  setText("clock-time", viewDataset.time?.clock || "--:--");
  setText("clock-date", viewDataset.time?.date || "Keine Datumsdaten");
  setText("phase-label", `${viewDataset.time?.phase || "Operation Phase"} / ${timeContext.timeOfDay} mode`);
  setText("light-mode", coupling.lightMode || viewDataset.assessment?.lightMode || "Adaptivlicht");
  setText("camera-status", viewDataset.telemetry?.cameraStatus || "No data");
  setText("wheel-contact", viewDataset.telemetry?.wheelContact || "No data");
  setText("cabin-state", viewDataset.telemetry?.cabinState || "No data");
  setText("weather-sensor", viewDataset.context?.weatherSensor || "No data");
  setText("input-summary", viewDataset.telemetry?.inputSummary || "No input data");
  setText("ai-title", viewDataset.assessment?.aiTitle || "Adaptive Support Strategy");
  setText("ai-summary", `${viewDataset.assessment?.aiSummary || narrative.aiSummary} ${coupling.linkedSummary}.`);
  setText("coffee-tag", `Break Support: ${coupling.coffeeRecommendation || viewDataset.assessment?.coffeeRecommendation || "No action"}`);
  setText("lighting-tag", `Lighting: ${coupling.lightMode || viewDataset.assessment?.lightMode || "No change"}`);
  setText("context-tag", `Mode ${coupling.drivingMode} / Driver ${derivedState.state} / Priority ${coupling.eventPriority}`);
  setText("warning-title", viewDataset.assessment?.warningTitle || "Warning State");
  setText("warning-priority", viewDataset.assessment?.warningPriority || "No priority");
  setText("warning-trigger", coupling.warningTrigger || viewDataset.assessment?.warningTrigger || "No trigger");
  setText("warning-action", `${viewDataset.assessment?.warningAction || narrative.warningAction} / ${coupling.strategy}`);
  setText("smart-context-status", viewDataset.context?.smartContextStatus || "Smart Context: Local Sync");
  if (isSystemReaction) {
    if (previousDriverState !== nextDriverState) {
      pushRuntimeEvent("state", "Driver State", `${previousDriverState || "init"} -> ${derivedState.state}`);
    }
    if (riskTrend.key === "rising" || derivedState.warningLevel === "ROT") {
      pushRuntimeEvent("risk", "Risk Alert", `Risk ${riskContext.finalRisk} / ${riskTrend.label} / ${coupling.supportLevel}`);
    }
    animateDashboardStateTransition(derivedState.state, riskTrend.key);
    triggerSystemReactionActivity(derivedState.state, riskTrend.key);
  }
  previousRenderedRiskScore = riskContext.finalRisk;

  setMetric("stress-value", "stress-bar", viewDataset.telemetry?.stress);
  setMetric("energy-value", "energy-bar", viewDataset.telemetry?.energy);
  setMetric("focus-value", "focus-bar", viewDataset.telemetry?.focus);
  applyHeartRateSensorDisplay(viewDataset);

  applyRiskMeter(riskContext.finalRisk, derivedState.theme);
  applyRiskInfluenceDisplay(riskContext);
  applyDayNightFeature(timeContext, sourceLabel);
  setModeMarker(riskContext.finalRisk);
  applyTheme(derivedState.theme);

  if (!document.getElementById("scan-overlay")?.hidden) {
    renderStateScan();
  }

  const dot = document.getElementById("system-status-dot");
  if (dot) {
    dot.style.background = viewDataset.system?.online ? "#5ef2a1" : "#ff4d6d";
    dot.style.color = viewDataset.system?.online ? "#5ef2a1" : "#ff4d6d";
  }

  const smartContextChip = document.getElementById("smart-context-status");
  if (smartContextChip) {
    smartContextChip.classList.toggle("is-connected", Boolean(viewDataset.context?.homeAssistantConnected));
  }

  const homeAssistantButton = document.getElementById("connect-home-assistant");
  if (homeAssistantButton) {
    homeAssistantButton.classList.toggle("is-connected", Boolean(viewDataset.context?.homeAssistantConnected));
  }
  renderHomeAssistantControls();

  updateScenarioStatus(Boolean(viewDataset.system?.overrideMode));
}

async function loadDashboardData() {
  if (window.__PORSCHE_ASSIST_DATA__) {
    backendRuntimeState = "online";
    baseSystemDataset = structuredClone(window.__PORSCHE_ASSIST_DATA__);
    renderDashboard(window.__PORSCHE_ASSIST_DATA__);
    syncScenarioInputs(baseSystemDataset);
    return;
  }

  try {
    const response = await fetch(BACKEND_ENDPOINT, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Backend antwortete mit ${response.status}`);
    }

    const payload = await response.json();
    backendRuntimeState = "online";
    baseSystemDataset = structuredClone(payload);
    renderDashboard(payload);
    syncScenarioInputs(baseSystemDataset);
  } catch (error) {
    console.info("Fallback auf Dummy-Daten:", error.message);
    backendRuntimeState = "offline";
    baseSystemDataset = structuredClone(FALLBACK_DATA);
    renderDashboard(FALLBACK_DATA);
    syncScenarioInputs(baseSystemDataset);
  }
}

function startClockTick() {
  setInterval(() => {
    const isHomeAssistantContext = currentDataset?.context?.timeSource === "home_assistant"
      && currentDataset?.context?.homeAssistantConnected;
    if (isHomeAssistantContext) return;

    const liveClock = document.getElementById("clock-time");
    if (!liveClock) return;

    const now = new Date();
    const currentClock = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
    liveClock.textContent = currentClock;

    const isOverride = document.getElementById("sim-override")?.checked;
    if (isOverride) return;

    const liveContext = deriveDayNightContext(currentClock);
    applyDayNightFeature(liveContext, "System Time");
    setText("phase-label", `${liveContext.phaseLabel} / ${liveContext.timeOfDay} mode`);
  }, 1000);
}

function setupDebugOverlay() {
  const toggle = document.getElementById("debug-overlay-toggle");
  const overlay = document.getElementById("debug-overlay");
  if (!toggle || !overlay) return;

  toggle.addEventListener("click", () => {
    const isOpen = overlay.hidden;
    overlay.hidden = !isOpen;
    toggle.classList.toggle("is-active", isOpen);
    toggle.setAttribute("aria-expanded", String(isOpen));
    document.body.classList.toggle("is-debug-overlay-open", isOpen);

    if (isOpen && currentDataset) {
      updateDebugOverlay({
        driverState: currentDataset.assessment?.driverState,
        riskIndex: document.getElementById("risk-score")?.textContent || currentDataset.assessment?.riskScore,
        drivingMode: currentDataset.assessment?.mode,
        homeAssistantConnected: Boolean(currentDataset.context?.homeAssistantConnected)
          || currentDataset.context?.timeSource === "home_assistant",
        mqttTopic: document.getElementById("mqtt-topic")?.textContent,
        lastEventTime: lastDebugEventTime,
      });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  pushRuntimeEvent("system", "System", "Timeline ready");
  loadDashboardData();
  startClockTick();
  setupScenarioInteraction();
  setupHomeAssistantIntegration();
  setupStateScan();
  setupDebugOverlay();
});

/*
Python-Integration:
1. Backend-Endpunkt auf BACKEND_ENDPOINT bereitstellen, z. B. per Flask/FastAPI.
2. JSON-Shape an FALLBACK_DATA anlehnen.
3. Alternativ Daten serverseitig vor dem Laden setzen:
   <script>window.__PORSCHE_ASSIST_DATA__ = {...};</script>
*/
