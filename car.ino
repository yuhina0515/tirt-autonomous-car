int  SPEED_CURVE;
int  TURN_OUTER_PWM;
int  TURN_INNER_PWM;
unsigned long  TURN_TIMEOUT_MS;
unsigned long  TURN_MIN_MS;
int  TURN_CAPTURE_PWM;
unsigned long  TURN_CAPTURE_GAP_MS;
int  turnCaptureGapPending;
unsigned long  turnCaptureGapAt;
unsigned long  turnCaptureGapElapsed;
int  turnCaptureSide;
int  turnDeparted;
int  turnCaptureStarted;
int  turnCaptureVisible;
unsigned long  TURN_MEMORY_MS;
unsigned long  TURN_CENTER_CLEAR_MS;
unsigned long  TURN_DIRECTION_CONFIRM_MS;
unsigned long  TURN_REACQUIRE_MS;
int  turnDirection;
int  turnActive;
int  turnFault;
int  LOSS_STOP_ENABLED;
unsigned long  SPLIT_CONFIRM_MS;
unsigned long  SPLIT_CLEAR_MS;
int  splitPending;
int  splitActive;
unsigned long  splitAt;
unsigned long  splitElapsed;
int  splitClearPending;
unsigned long  splitClearAt;
unsigned long  splitClearElapsed;
int  OUTER_TURN_ASSIST;
int  OUTER_LINE_THRESHOLD;
int  OUTER_BACKGROUND_THRESHOLD;
unsigned long  OUTER_CONFIRM_MS;
unsigned long  OUTER_MEMORY_MS;
unsigned long  OUTER_PROBE_TIMEOUT_MS;
unsigned long  OUTER_OVERRIDE_WINDOW_MS;
int  outerCandidate;
unsigned long  outerCandidateAt;
unsigned long  outerCandidateElapsed;
int  outerDirection;
unsigned long  outerSeenAt;
unsigned long  outerAge;
int  outerReady;
int  outerProbeActive;
unsigned long  outerProbeAt;
unsigned long  outerProbeElapsed;
int  turnDirectionSource;
int  turnConfirm;
unsigned long  turnCaptureAt;
unsigned long  turnCaptureElapsed;
unsigned long  turnNow;
unsigned long  turnAt;
unsigned long  turnSeenAt;
unsigned long  turnElapsed;
unsigned long  turnAge;
int  centerPending;
unsigned long  centerAt;
unsigned long  centerElapsed;
int  turnCandidate;
unsigned long  turnCandidateAt;
unsigned long  turnCandidateElapsed;
int  GAP_PWM;
unsigned long  GAP_DIRECTION_MS;
int  gapDirection;
unsigned long  gapDirectionAt;
unsigned long  gapDirectionAge;
unsigned long  GAP_TIMEOUT_MS;
int  gapActive;
unsigned long  gapAt;
unsigned long  gapElapsed;
int  gapConfirm;
unsigned long  GAP_REACQUIRE_MS;
unsigned long  gapCaptureAt;
unsigned long  gapCaptureElapsed;
int  DEBUG_SERIAL;
unsigned long  TELEMETRY_PERIOD_MS;
unsigned long  telemetryAt;
unsigned long  telemetryElapsed;
int  ledStatus;
int  ledDesired;
unsigned long  STRAIGHT_STAGE2_MS;
unsigned long  STRAIGHT_STAGE3_MS;
unsigned long  STRAIGHT_STAGE4_MS;
int  STRAIGHT_STAGE2_PWM;
int  STRAIGHT_STAGE3_PWM;
int  STRAIGHT_STAGE1_PWM;
int  STRAIGHT_TRIM_PWM;
unsigned long  STRAIGHT_TRIM_MAX_MS;
unsigned long  STRAIGHT_TRIM_CENTER_MS;
int  straightPending;
unsigned long  straightElapsed;
unsigned long  straightLastAt;
unsigned long  straightDelta;
int  straightTrimPending;
unsigned long  straightTrimAt;
unsigned long  straightTrimElapsed;
int  straightTrimCenterPending;
unsigned long  straightTrimCenterAt;
unsigned long  straightTrimCenterElapsed;
int  straightTrimAllowed;
int  straightWarning;
int  straightTrimSlow;
int  straightTrimInner;
int  straightPwm;
unsigned long  MIN_LAP_MS;
unsigned long  MAX_LAP_MS;
unsigned long  DEPART_CONFIRM_MS;
unsigned long  FINISH_CONFIRM_MS;
unsigned long  WIDE_TIMEOUT_MS;
int  WIDE_PWM;
int  lapStarted;
int  lapReady;
int  lapDone;
unsigned long  lapAt;
unsigned long  lapElapsed;
int  departPending;
unsigned long  departAt;
unsigned long  departElapsed;
int  wideActive;
unsigned long  wideAt;
unsigned long  wideElapsed;
int  LIFT_ENABLED;
int  LIFT_CROSSING_INDEX;
unsigned long  LIFT_MARKER_CONFIRM_MS;
unsigned long  LIFT_CLEAR_CONFIRM_MS;
unsigned long  LIFT_WAIT_MS;
int  LIFT_AUTO_EXIT;
int  LIFT_EXIT_PWM;
unsigned long  LIFT_EXIT_TIMEOUT_MS;
int  liftState;
int  liftCrossings;
int  liftMarkerLatched;
int  liftMarkerPending;
int  liftMarkerArmed;
unsigned long  liftMarkerAt;
unsigned long  liftMarkerElapsed;
int  liftClearPending;
unsigned long  liftClearAt;
unsigned long  liftClearElapsed;
unsigned long  liftWaitAt;
unsigned long  liftWaitElapsed;
unsigned long  liftExitAt;
unsigned long  liftExitElapsed;
int  liftExitPending;
unsigned long  liftLineAt;
unsigned long  liftLineElapsed;
int  LINE_THRESHOLD;
int  SPEED_STRAIGHT;
int  sensorA1;
int  sensorA2;
int  sensorA3;
int  sensorA4;
int  sensorA5;
int  SPEED_TURN_INNER_MEDIUM;
int  sensorF;
int  WHITE_STOP_COUNT;
int  whiteCount;
int  sumW;
int  countOn;
int  absW;
int  innerSpeed;
int  TURN_KP;
int  rawA1;
int  rawA2;
int  rawA3;
int  rawA4;
int  rawA5;
#include <moto_NeoPixel.h>
moto_NeoPixel strip13= moto_NeoPixel(2,13, NEO_GRB + NEO_KHZ800);
void colorled13(int number,String c)
{
	long rgb_number = strtol(&c[1], NULL, 16);
   int r = rgb_number >> 16;
   int g = rgb_number >> 8 & 0xFF;
   int b = rgb_number & 0xFF;
   if(number <= 0) number = 0;
      else  number--;
   strip13.setPixelColor(number,strip13.Color(r,g,b));
   strip13.show();
}

/**
 * 描述此函式...
 */
void stop2() {
  digitalWrite(7,LOW);
  analogWrite(5,0);
  digitalWrite(4,HIGH);
  analogWrite(6,0);
}

/**
 * A1=right/A5=left outer assistance. Center-only search
 * gets at most150ms to capture line or receive confirmed
 * outer support; otherwise stop. Outer evidence may
 * correct it once without resetting the800ms total
 * deadline. Confirmed outer plus matching F2/F8 starts
 * before full loss. Outer forward150/inner reverse114;
 * After actual loss, matching single edge also starts capture
 * at100/20 or100/50. Active-turn F14 and post-capture F0
 * share a fixed60ms forward-only uncertainty budget; normal
 * lift/finish marker handling is unchanged. Split F10 uses
 * its own bounded confirmation. The150ms unsupported-search
 * cutoff applies only before capture; the800ms total deadline
 * stays fixed. Continuous15ms capture completes turn.
 */
void sharp_turn() {
  turnElapsed = turnNow - turnAt;
  if (sensorF == 0) {
    turnDeparted = 1;
  }
  if (sensorF == 4 || sensorF == 6 || sensorF == 12 || (turnDeparted == 1 || turnCaptureStarted == 1) && ((turnCaptureStarted == 1 || turnDirection == 1) && sensorF == 2 || (turnCaptureStarted == 1 || turnDirection == -1) && sensorF == 8)) {
    turnCaptureVisible = 1;
  } else {
    turnCaptureVisible = 0;
  }
  if (turnDirectionSource == 0 && turnElapsed <= OUTER_OVERRIDE_WINDOW_MS && outerReady == 1) {
    turnDirection = outerDirection;
    turnDirectionSource = 1;
  }
  if (turnElapsed >= TURN_TIMEOUT_MS || OUTER_TURN_ASSIST == 1 && turnDirectionSource == 0 && turnCaptureStarted == 0 && turnCaptureVisible == 0 && turnElapsed >= OUTER_OVERRIDE_WINDOW_MS) {
    if (LOSS_STOP_ENABLED == 0 && sensorF == 0) {
      if (outerReady == 1) {
        gapDirection = outerDirection;
        gapDirectionAt = outerSeenAt;
      } else if (gapActive == 0 && turnActive == 1 && turnDirection != 0) {
        gapDirection = turnDirection;
        gapDirectionAt = turnNow;
      } else if (gapActive == 0 && turnDirection != 0 && turnAge <= TURN_MEMORY_MS) {
        gapDirection = turnDirection;
        gapDirectionAt = turnSeenAt;
      } else {
        if (gapActive == 0) {
          gapDirection = 0;
        }
      }
      gapDirectionAge = turnNow - gapDirectionAt;
      turnActive = 0;
      turnDirection = 0;
      outerProbeActive = 0;
      gapActive = 1;
      gapAt = turnNow;
      gapConfirm = 0;
      whiteCount = 0;
      if (gapDirection == -1 && gapDirectionAge <= GAP_DIRECTION_MS) {
        digitalWrite(7,LOW);
        analogWrite(5,15);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (gapDirection == 1 && gapDirectionAge <= GAP_DIRECTION_MS) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,15);
      } else {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      }
    } else {
      turnFault = 1;
      turnActive = 0;
      stop2();
    }
  } else {
    if (turnElapsed >= TURN_MIN_MS && turnCaptureVisible == 1) {
      turnCaptureStarted = 1;
      if (sensorF == 8 || sensorF == 12) {
        turnCaptureSide = -1;
      } else if (sensorF == 2 || sensorF == 6) {
        turnCaptureSide = 1;
      } else {
        turnCaptureSide = 0;
      }
      if (turnConfirm == 0) {
        turnConfirm = 1;
        turnCaptureAt = turnNow;
      }
      turnCaptureElapsed = turnNow - turnCaptureAt;
    } else {
      turnConfirm = 0;
    }
    if ((sensorF == 4 || sensorF == 6 || sensorF == 12) && turnConfirm == 1 && turnCaptureElapsed >= TURN_REACQUIRE_MS) {
      turnActive = 0;
      turnDirection = 0;
      turnConfirm = 0;
      whiteCount = 0;
      if (sensorF == 8) {
        digitalWrite(7,LOW);
        analogWrite(5,20);
        digitalWrite(4,HIGH);
        analogWrite(6,TURN_CAPTURE_PWM);
      } else if (sensorF == 12) {
        digitalWrite(7,LOW);
        analogWrite(5,50);
        digitalWrite(4,HIGH);
        analogWrite(6,TURN_CAPTURE_PWM);
      } else if (sensorF == 2) {
        digitalWrite(7,LOW);
        analogWrite(5,TURN_CAPTURE_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,20);
      } else if (sensorF == 6) {
        digitalWrite(7,LOW);
        analogWrite(5,TURN_CAPTURE_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,50);
      } else {
        digitalWrite(7,LOW);
        analogWrite(5,TURN_CAPTURE_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,TURN_CAPTURE_PWM);
      }
    } else {
      if (turnConfirm >= 1) {
        if (sensorF == 8) {
          digitalWrite(7,LOW);
          analogWrite(5,20);
          digitalWrite(4,HIGH);
          analogWrite(6,TURN_CAPTURE_PWM);
        } else if (sensorF == 12) {
          digitalWrite(7,LOW);
          analogWrite(5,50);
          digitalWrite(4,HIGH);
          analogWrite(6,TURN_CAPTURE_PWM);
        } else if (sensorF == 2) {
          digitalWrite(7,LOW);
          analogWrite(5,TURN_CAPTURE_PWM);
          digitalWrite(4,HIGH);
          analogWrite(6,20);
        } else if (sensorF == 6) {
          digitalWrite(7,LOW);
          analogWrite(5,TURN_CAPTURE_PWM);
          digitalWrite(4,HIGH);
          analogWrite(6,50);
        } else {
          digitalWrite(7,LOW);
          analogWrite(5,TURN_CAPTURE_PWM);
          digitalWrite(4,HIGH);
          analogWrite(6,TURN_CAPTURE_PWM);
        }
      } else {
        if (turnCaptureStarted == 1) {
          if (sensorF == 0 || sensorF == 14) {
            if (turnCaptureGapPending == 0) {
              turnCaptureGapPending = 1;
              turnCaptureGapAt = turnNow;
            }
            turnCaptureGapElapsed = turnNow - turnCaptureGapAt;
            if (turnCaptureGapElapsed >= TURN_CAPTURE_GAP_MS) {
              if (LOSS_STOP_ENABLED == 0 && sensorF == 0) {
                if (outerReady == 1) {
                  gapDirection = outerDirection;
                  gapDirectionAt = outerSeenAt;
                } else if (gapActive == 0 && turnActive == 1 && turnDirection != 0) {
                  gapDirection = turnDirection;
                  gapDirectionAt = turnNow;
                } else if (gapActive == 0 && turnDirection != 0 && turnAge <= TURN_MEMORY_MS) {
                  gapDirection = turnDirection;
                  gapDirectionAt = turnSeenAt;
                } else {
                  if (gapActive == 0) {
                    gapDirection = 0;
                  }
                }
                gapDirectionAge = turnNow - gapDirectionAt;
                turnActive = 0;
                turnDirection = 0;
                outerProbeActive = 0;
                gapActive = 1;
                gapAt = turnNow;
                gapConfirm = 0;
                whiteCount = 0;
                if (gapDirection == -1 && gapDirectionAge <= GAP_DIRECTION_MS) {
                  digitalWrite(7,LOW);
                  analogWrite(5,15);
                  digitalWrite(4,HIGH);
                  analogWrite(6,GAP_PWM);
                } else if (gapDirection == 1 && gapDirectionAge <= GAP_DIRECTION_MS) {
                  digitalWrite(7,LOW);
                  analogWrite(5,GAP_PWM);
                  digitalWrite(4,HIGH);
                  analogWrite(6,15);
                } else {
                  digitalWrite(7,LOW);
                  analogWrite(5,GAP_PWM);
                  digitalWrite(4,HIGH);
                  analogWrite(6,GAP_PWM);
                }
              } else {
                turnFault = 1;
                turnActive = 0;
                stop2();
              }
            } else {
              if (turnCaptureSide == -1) {
                digitalWrite(7,LOW);
                analogWrite(5,30);
                digitalWrite(4,HIGH);
                analogWrite(6,60);
              } else if (turnCaptureSide == 1) {
                digitalWrite(7,LOW);
                analogWrite(5,60);
                digitalWrite(4,HIGH);
                analogWrite(6,30);
              } else {
                digitalWrite(7,LOW);
                analogWrite(5,45);
                digitalWrite(4,HIGH);
                analogWrite(6,45);
              }
            }
          } else {
            turnFault = 1;
            turnActive = 0;
            stop2();
          }
        } else {
          if (sensorF == 14) {
            if (turnCaptureGapPending == 0) {
              turnCaptureGapPending = 1;
              turnCaptureGapAt = turnNow;
            }
            turnCaptureGapElapsed = turnNow - turnCaptureGapAt;
            if (turnCaptureGapElapsed >= TURN_CAPTURE_GAP_MS) {
              if (LOSS_STOP_ENABLED == 0 && sensorF == 0) {
                if (outerReady == 1) {
                  gapDirection = outerDirection;
                  gapDirectionAt = outerSeenAt;
                } else if (gapActive == 0 && turnActive == 1 && turnDirection != 0) {
                  gapDirection = turnDirection;
                  gapDirectionAt = turnNow;
                } else if (gapActive == 0 && turnDirection != 0 && turnAge <= TURN_MEMORY_MS) {
                  gapDirection = turnDirection;
                  gapDirectionAt = turnSeenAt;
                } else {
                  if (gapActive == 0) {
                    gapDirection = 0;
                  }
                }
                gapDirectionAge = turnNow - gapDirectionAt;
                turnActive = 0;
                turnDirection = 0;
                outerProbeActive = 0;
                gapActive = 1;
                gapAt = turnNow;
                gapConfirm = 0;
                whiteCount = 0;
                if (gapDirection == -1 && gapDirectionAge <= GAP_DIRECTION_MS) {
                  digitalWrite(7,LOW);
                  analogWrite(5,15);
                  digitalWrite(4,HIGH);
                  analogWrite(6,GAP_PWM);
                } else if (gapDirection == 1 && gapDirectionAge <= GAP_DIRECTION_MS) {
                  digitalWrite(7,LOW);
                  analogWrite(5,GAP_PWM);
                  digitalWrite(4,HIGH);
                  analogWrite(6,15);
                } else {
                  digitalWrite(7,LOW);
                  analogWrite(5,GAP_PWM);
                  digitalWrite(4,HIGH);
                  analogWrite(6,GAP_PWM);
                }
              } else {
                turnFault = 1;
                turnActive = 0;
                stop2();
              }
            } else {
              if (turnCaptureSide == -1) {
                digitalWrite(7,LOW);
                analogWrite(5,30);
                digitalWrite(4,HIGH);
                analogWrite(6,60);
              } else if (turnCaptureSide == 1) {
                digitalWrite(7,LOW);
                analogWrite(5,60);
                digitalWrite(4,HIGH);
                analogWrite(6,30);
              } else {
                digitalWrite(7,LOW);
                analogWrite(5,45);
                digitalWrite(4,HIGH);
                analogWrite(6,45);
              }
            }
          } else {
            if (turnDirection == -1) {
              digitalWrite(7,HIGH);
              analogWrite(5,TURN_INNER_PWM);
              digitalWrite(4,HIGH);
              analogWrite(6,TURN_OUTER_PWM);
            } else {
              digitalWrite(7,LOW);
              analogWrite(5,TURN_OUTER_PWM);
              digitalWrite(4,LOW);
              analogWrite(6,TURN_INNER_PWM);
            }
          }
        }
      }
    }
  }
}

/**
 * Gap base45. Qualified retained right direction uses45/15,
 * left15/45, for at most120ms without fresh evidence; renewal does
 * not refresh direction age. Unknown/expired direction uses45/45.
 * Normal120ms deadline remains; LOSS_STOP_ENABLED0 uses forward
 * fallback instead of F0 fault. Side-line return starts differential
 * capture20/45 or30/45 immediately. Continuous narrow line15ms
 * finishes; invalid observations reset confirmation, not
 * the event deadline. Wide line returns to marker handling.
 */
void cross_gap() {
  gapElapsed = turnNow - gapAt;
  if (outerReady == 1) {
    gapDirection = outerDirection;
    gapDirectionAt = outerSeenAt;
  } else if (sensorF == 2 || sensorF == 6) {
    gapDirection = 1;
    gapDirectionAt = turnNow;
  } else if (sensorF == 8 || sensorF == 12) {
    gapDirection = -1;
    gapDirectionAt = turnNow;
  }
  gapDirectionAge = turnNow - gapDirectionAt;
  if (gapElapsed >= GAP_TIMEOUT_MS) {
    if (LOSS_STOP_ENABLED == 0 && sensorF == 0) {
      if (outerReady == 1) {
        gapDirection = outerDirection;
        gapDirectionAt = outerSeenAt;
      } else if (gapActive == 0 && turnActive == 1 && turnDirection != 0) {
        gapDirection = turnDirection;
        gapDirectionAt = turnNow;
      } else if (gapActive == 0 && turnDirection != 0 && turnAge <= TURN_MEMORY_MS) {
        gapDirection = turnDirection;
        gapDirectionAt = turnSeenAt;
      } else {
        if (gapActive == 0) {
          gapDirection = 0;
        }
      }
      gapDirectionAge = turnNow - gapDirectionAt;
      turnActive = 0;
      turnDirection = 0;
      outerProbeActive = 0;
      gapActive = 1;
      gapAt = turnNow;
      gapConfirm = 0;
      whiteCount = 0;
      if (gapDirection == -1 && gapDirectionAge <= GAP_DIRECTION_MS) {
        digitalWrite(7,LOW);
        analogWrite(5,15);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (gapDirection == 1 && gapDirectionAge <= GAP_DIRECTION_MS) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,15);
      } else {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      }
    } else {
      turnFault = 1;
      gapActive = 0;
      stop2();
    }
  } else {
    if (sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12) {
      if (gapConfirm == 0) {
        gapConfirm = 1;
        gapCaptureAt = turnNow;
      }
      gapCaptureElapsed = turnNow - gapCaptureAt;
    } else {
      gapConfirm = 0;
    }
    if (gapConfirm == 1 && gapCaptureElapsed >= GAP_REACQUIRE_MS || sensorF == 14) {
      gapActive = 0;
      turnDirection = 0;
      whiteCount = 0;
      if (sensorF == 8) {
        digitalWrite(7,LOW);
        analogWrite(5,20);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (sensorF == 12) {
        digitalWrite(7,LOW);
        analogWrite(5,30);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (sensorF == 2) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,20);
      } else if (sensorF == 6) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,30);
      } else {
        if (sensorF == 0) {
          if (gapDirection == -1 && gapDirectionAge <= GAP_DIRECTION_MS) {
            digitalWrite(7,LOW);
            analogWrite(5,15);
            digitalWrite(4,HIGH);
            analogWrite(6,GAP_PWM);
          } else if (gapDirection == 1 && gapDirectionAge <= GAP_DIRECTION_MS) {
            digitalWrite(7,LOW);
            analogWrite(5,GAP_PWM);
            digitalWrite(4,HIGH);
            analogWrite(6,15);
          } else {
            digitalWrite(7,LOW);
            analogWrite(5,GAP_PWM);
            digitalWrite(4,HIGH);
            analogWrite(6,GAP_PWM);
          }
        } else {
          digitalWrite(7,LOW);
          analogWrite(5,GAP_PWM);
          digitalWrite(4,HIGH);
          analogWrite(6,GAP_PWM);
        }
      }
    } else {
      if (sensorF == 8) {
        digitalWrite(7,LOW);
        analogWrite(5,20);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (sensorF == 12) {
        digitalWrite(7,LOW);
        analogWrite(5,30);
        digitalWrite(4,HIGH);
        analogWrite(6,GAP_PWM);
      } else if (sensorF == 2) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,20);
      } else if (sensorF == 6) {
        digitalWrite(7,LOW);
        analogWrite(5,GAP_PWM);
        digitalWrite(4,HIGH);
        analogWrite(6,30);
      } else {
        if (sensorF == 0) {
          if (gapDirection == -1 && gapDirectionAge <= GAP_DIRECTION_MS) {
            digitalWrite(7,LOW);
            analogWrite(5,15);
            digitalWrite(4,HIGH);
            analogWrite(6,GAP_PWM);
          } else if (gapDirection == 1 && gapDirectionAge <= GAP_DIRECTION_MS) {
            digitalWrite(7,LOW);
            analogWrite(5,GAP_PWM);
            digitalWrite(4,HIGH);
            analogWrite(6,15);
          } else {
            digitalWrite(7,LOW);
            analogWrite(5,GAP_PWM);
            digitalWrite(4,HIGH);
            analogWrite(6,GAP_PWM);
          }
        } else {
          digitalWrite(7,LOW);
          analogWrite(5,GAP_PWM);
          digitalWrite(4,HIGH);
          analogWrite(6,GAP_PWM);
        }
      }
    }
  }
}

/**
 * Lift: wide F14 confirms30ms but only arms a candidate.
 * First non-wide sample must be centered F4 with no outer turn
 * evidence; side/loss/split or active turn/gap cancels. Stop
 * immediately on qualifying centered exit; user-requested wait23350ms
 * from stop command, not measured settled feedback. This is below
 * the published27s +/-5% timing. Auto exit PWM45 with1500ms limit.
 * Consume marker once. PWM zero is not active braking. Disable
 * LIFT_ENABLED for the earlier practice mat without a lift.
 */
void lift_control() {
  if (liftState == 1) {
    stop2();
    liftWaitElapsed = turnNow - liftWaitAt;
    if (LIFT_AUTO_EXIT == 1 && liftWaitElapsed >= LIFT_WAIT_MS) {
      liftState = 2;
      liftExitAt = turnNow;
      liftExitPending = 0;
    }
  } else if (liftState == 2) {
    liftExitElapsed = turnNow - liftExitAt;
    if (liftExitElapsed >= LIFT_EXIT_TIMEOUT_MS) {
      turnFault = 1;
      stop2();
    } else {
      if (sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12) {
        if (liftExitPending == 0) {
          liftExitPending = 1;
          liftLineAt = turnNow;
        }
        liftLineElapsed = turnNow - liftLineAt;
        if (liftLineElapsed >= LIFT_CLEAR_CONFIRM_MS) {
          liftState = 3;
          turnDirection = 0;
          turnCandidate = 0;
          centerPending = 0;
          wideActive = 0;
          whiteCount = 0;
        }
      } else {
        liftExitPending = 0;
      }
      digitalWrite(7,LOW);
      analogWrite(5,LIFT_EXIT_PWM);
      digitalWrite(4,HIGH);
      analogWrite(6,LIFT_EXIT_PWM);
    }
  }
}

/**
 * LED updates only on changes. Green=running; blue=outer-direction
 * probe stop, lift wait, fault or finish. No per-loop NeoPixel show.
 */
void update_status_led() {
  ledDesired = 1;
  if (outerProbeActive == 1 || turnFault == 1 || lapDone == 1 || liftState == 1) {
    ledDesired = 2;
  }
  if (ledDesired == ledStatus) {
  } else {
    if (ledDesired == 2) {
      colorled13(1,"#0000ff");
    } else {
      colorled13(1,"#33ff33");
    }
    ledStatus = ledDesired;
  }
}

void setup()
{
  Serial.begin(115200);
  strip13.begin();
  strip13.show();
  pinMode(12, INPUT);
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  pinMode(A3, INPUT);
  pinMode(A4, INPUT);
  pinMode(A5, INPUT);
  pinMode(7, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(6, OUTPUT);
    SPEED_CURVE = 174;
  TURN_OUTER_PWM = 150;
  TURN_INNER_PWM = 114;
  TURN_TIMEOUT_MS = 800;
  TURN_MIN_MS = 30;
  TURN_CAPTURE_PWM = 100;
  TURN_CAPTURE_GAP_MS = 60;
  turnCaptureGapPending = 0;
  turnCaptureGapAt = 0;
  turnCaptureGapElapsed = 0;
  turnCaptureSide = 0;
  turnDeparted = 0;
  turnCaptureStarted = 0;
  turnCaptureVisible = 0;
  TURN_MEMORY_MS = 250;
  TURN_CENTER_CLEAR_MS = 80;
  TURN_DIRECTION_CONFIRM_MS = 15;
  TURN_REACQUIRE_MS = 15;
  turnDirection = 0;
  turnActive = 0;
  turnFault = 0;
  LOSS_STOP_ENABLED = 0;
  SPLIT_CONFIRM_MS = 20;
  SPLIT_CLEAR_MS = 15;
  splitPending = 0;
  splitActive = 0;
  splitAt = 0;
  splitElapsed = 0;
  splitClearPending = 0;
  splitClearAt = 0;
  splitClearElapsed = 0;
  OUTER_TURN_ASSIST = 1;
  OUTER_LINE_THRESHOLD = 70;
  OUTER_BACKGROUND_THRESHOLD = 120;
  OUTER_CONFIRM_MS = 20;
  OUTER_MEMORY_MS = 120;
  OUTER_PROBE_TIMEOUT_MS = 80;
  OUTER_OVERRIDE_WINDOW_MS = 150;
  outerCandidate = 0;
  outerCandidateAt = 0;
  outerCandidateElapsed = 0;
  outerDirection = 0;
  outerSeenAt = 0;
  outerAge = 0;
  outerReady = 0;
  outerProbeActive = 0;
  outerProbeAt = 0;
  outerProbeElapsed = 0;
  turnDirectionSource = 0;
  turnConfirm = 0;
  turnCaptureAt = 0;
  turnCaptureElapsed = 0;
  turnNow = 0;
  turnAt = 0;
  turnSeenAt = 0;
  turnElapsed = 0;
  turnAge = 0;
  centerPending = 0;
  centerAt = 0;
  centerElapsed = 0;
  turnCandidate = 0;
  turnCandidateAt = 0;
  turnCandidateElapsed = 0;
  GAP_PWM = 45;
  GAP_DIRECTION_MS = 120;
  gapDirection = 0;
  gapDirectionAt = 0;
  gapDirectionAge = 0;
  GAP_TIMEOUT_MS = 120;
  gapActive = 0;
  gapAt = 0;
  gapElapsed = 0;
  gapConfirm = 0;
  GAP_REACQUIRE_MS = 15;
  gapCaptureAt = 0;
  gapCaptureElapsed = 0;
  DEBUG_SERIAL = 0;
  TELEMETRY_PERIOD_MS = 50;
  telemetryAt = 0;
  telemetryElapsed = 0;
  ledStatus = 1;
  ledDesired = 1;
  STRAIGHT_STAGE2_MS = 200;
  STRAIGHT_STAGE3_MS = 500;
  STRAIGHT_STAGE4_MS = 900;
  STRAIGHT_STAGE2_PWM = 150;
  STRAIGHT_STAGE3_PWM = 190;
  STRAIGHT_STAGE1_PWM = 100;
  STRAIGHT_TRIM_PWM = 30;
  STRAIGHT_TRIM_MAX_MS = 30;
  STRAIGHT_TRIM_CENTER_MS = 30;
  straightPending = 0;
  straightElapsed = 0;
  straightLastAt = 0;
  straightDelta = 0;
  straightTrimPending = 0;
  straightTrimAt = 0;
  straightTrimElapsed = 0;
  straightTrimCenterPending = 0;
  straightTrimCenterAt = 0;
  straightTrimCenterElapsed = 0;
  straightTrimAllowed = 0;
  straightWarning = 0;
  straightTrimSlow = 0;
  straightTrimInner = 70;
  straightPwm = 100;
  MIN_LAP_MS = 15000;
  MAX_LAP_MS = 180000;
  DEPART_CONFIRM_MS = 100;
  FINISH_CONFIRM_MS = 250;
  WIDE_TIMEOUT_MS = 900;
  WIDE_PWM = 45;
  lapStarted = 0;
  lapReady = 0;
  lapDone = 0;
  lapAt = 0;
  lapElapsed = 0;
  departPending = 0;
  departAt = 0;
  departElapsed = 0;
  wideActive = 0;
  wideAt = 0;
  wideElapsed = 0;
  LIFT_ENABLED = 1;
  LIFT_CROSSING_INDEX = 1;
  LIFT_MARKER_CONFIRM_MS = 30;
  LIFT_CLEAR_CONFIRM_MS = 100;
  LIFT_WAIT_MS = 23350;
  LIFT_AUTO_EXIT = 1;
  LIFT_EXIT_PWM = 45;
  LIFT_EXIT_TIMEOUT_MS = 1500;
  liftState = 0;
  liftCrossings = 0;
  liftMarkerLatched = 0;
  liftMarkerPending = 0;
  liftMarkerArmed = 0;
  liftMarkerAt = 0;
  liftMarkerElapsed = 0;
  liftClearPending = 0;
  liftClearAt = 0;
  liftClearElapsed = 0;
  liftWaitAt = 0;
  liftWaitElapsed = 0;
  liftExitAt = 0;
  liftExitElapsed = 0;
  liftExitPending = 0;
  liftLineAt = 0;
  liftLineElapsed = 0;
  LINE_THRESHOLD = 70;
  SPEED_STRAIGHT = 230;
  sensorA1 = 0;
  sensorA2 = 0;
  sensorA3 = 0;
  sensorA4 = 0;
  sensorA5 = 0;
  SPEED_TURN_INNER_MEDIUM = 15;
  sensorF = 0;
  WHITE_STOP_COUNT = 40;
  whiteCount = 0;
  sumW = 0;
  countOn = 0;
  absW = 0;
  innerSpeed = 0;
  TURN_KP = 174;
  rawA1 = 0;
  rawA2 = 0;
  rawA3 = 0;
  rawA4 = 0;
  rawA5 = 0;
  colorled13(1,"#0000ff");
  while ((digitalRead(12) == 1)) {
    delay(20);
  }
  colorled13(1,"#33ff33");

}


void loop()
{
  // Start on the narrow line LEFT of the large finish patch,
  // facing away from finish. Three-center-sensor control,
  // sharp corners and short gaps. After departure/minimum
  // run, sustained wide line latches finish stop. This is not
  // measured lap localization. Button waits at boot only.
    // Read all five ADCs; preserve original raw telemetry.
    sensorA1 = analogRead(A1);
    sensorA2 = analogRead(A2);
    sensorA3 = analogRead(A3);
    sensorA4 = analogRead(A4);
    sensorA5 = analogRead(A5);
    rawA1 = sensorA1;
    rawA2 = sensorA2;
    rawA3 = sensorA3;
    rawA4 = sensorA4;
    rawA5 = sensorA5;
    // Exclude A1/A5 from center F and weighted position. Their saved raw
    // values now feed the separately confirmed outer sharp-turn assistance.
    sensorA1 = 1023;
    sensorA5 = 1023;
    // Build F = 8*A4_on + 4*A3_on + 2*A2_on.
    sensorF = 0;
    if (sensorA2 < LINE_THRESHOLD) {
      sensorF = sensorF + 2;
    }
    if (sensorA3 < LINE_THRESHOLD) {
      sensorF = sensorF + 4;
    }
    if (sensorA4 < LINE_THRESHOLD) {
      sensorF = sensorF + 8;
    }
    // Curve base174/gain174/minimum15 after45 percent increase
    // from120/120/10. Straight stages100/150/190/230 retain brief
    // F6/F12 trim without advancing during correction. Mild trim
    // pauses stages; stable center restores retained stage.
    // Strong side or confirmed outer resets stages.
    sumW = 0;
    countOn = 0;
    if (sensorA2 < LINE_THRESHOLD) {
      sumW = sumW + 1;
      countOn = countOn + 1;
    }
    if (sensorA3 < LINE_THRESHOLD) {
      countOn = countOn + 1;
    }
    if (sensorA4 < LINE_THRESHOLD) {
      sumW = sumW + -1;
      countOn = countOn + 1;
    }
    absW = sumW;
    if (sumW < 0) {
      absW = 0 - sumW;
    }
    if (countOn > 0) {
      innerSpeed = SPEED_CURVE - (absW * TURN_KP) / countOn;
    }
    if (innerSpeed < SPEED_TURN_INNER_MEDIUM) {
      innerSpeed = SPEED_TURN_INNER_MEDIUM;
    }
    turnNow = millis();
    splitActive = 0;
    if ((liftState == 0 || liftState == 3) && gapActive == 0 && turnFault == 0 && lapDone == 0) {
      if (sensorF == 10) {
        splitActive = 1;
        splitClearPending = 0;
        if (splitPending == 0) {
          splitPending = 1;
          splitAt = turnNow;
        }
        splitElapsed = turnNow - splitAt;
        if (splitElapsed >= SPLIT_CONFIRM_MS) {
          turnFault = 1;
        }
      } else {
        if (splitPending == 1 && (sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12)) {
          if (splitClearPending == 0) {
            splitClearPending = 1;
            splitClearAt = turnNow;
          }
          splitClearElapsed = turnNow - splitClearAt;
          if (splitClearElapsed >= SPLIT_CLEAR_MS) {
            splitPending = 0;
            splitClearPending = 0;
          }
        } else {
          splitClearPending = 0;
        }
      }
    } else {
      splitPending = 0;
      splitClearPending = 0;
    }
    if (sensorF != 0) {
      outerProbeActive = 0;
    }
    if (OUTER_TURN_ASSIST == 1 && (sensorF == 0 || sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12)) {
      if (rawA1 < OUTER_LINE_THRESHOLD && rawA5 >= OUTER_BACKGROUND_THRESHOLD) {
        if (outerCandidate != 1) {
          outerCandidate = 1;
          outerCandidateAt = turnNow;
        }
        outerCandidateElapsed = turnNow - outerCandidateAt;
        if (outerCandidateElapsed >= OUTER_CONFIRM_MS) {
          outerDirection = 1;
          outerSeenAt = turnNow;
        }
      } else if (rawA5 < OUTER_LINE_THRESHOLD && rawA1 >= OUTER_BACKGROUND_THRESHOLD) {
        if (outerCandidate != -1) {
          outerCandidate = -1;
          outerCandidateAt = turnNow;
        }
        outerCandidateElapsed = turnNow - outerCandidateAt;
        if (outerCandidateElapsed >= OUTER_CONFIRM_MS) {
          outerDirection = -1;
          outerSeenAt = turnNow;
        }
      } else {
        outerCandidate = 0;
      }
      if (rawA1 < OUTER_LINE_THRESHOLD && rawA5 < OUTER_LINE_THRESHOLD) {
        outerDirection = 0;
      }
    } else {
      outerCandidate = 0;
      outerDirection = 0;
    }
    outerAge = turnNow - outerSeenAt;
    outerReady = 0;
    if (OUTER_TURN_ASSIST == 1 && outerDirection != 0 && outerAge <= OUTER_MEMORY_MS && (outerCandidate == 0 || outerCandidate == outerDirection)) {
      outerReady = 1;
    }
    straightDelta = turnNow - straightLastAt;
    straightLastAt = turnNow;
    straightTrimAllowed = 0;
    straightWarning = 0;
    if (outerReady == 0 && (liftState == 0 || liftState == 3) && turnActive == 0 && gapActive == 0 && turnFault == 0 && lapDone == 0) {
      if (outerCandidate != 0 && (sensorF == 4 || sensorF == 6 || sensorF == 12)) {
        straightWarning = 1;
        straightTrimSlow = 1;
        straightTrimPending = 1;
        straightTrimCenterPending = 0;
        straightTrimAt = turnNow - STRAIGHT_TRIM_MAX_MS;
      } else {
        if (sensorF == 4) {
          if (straightPending == 0) {
            straightPending = 1;
            straightElapsed = 0;
            straightDelta = 0;
            straightPwm = STRAIGHT_STAGE1_PWM;
          }
          if (straightTrimPending == 1) {
            if (straightTrimCenterPending == 0) {
              straightTrimCenterPending = 1;
              straightTrimCenterAt = turnNow;
            }
            straightTrimCenterElapsed = turnNow - straightTrimCenterAt;
            straightTrimElapsed = turnNow - straightTrimAt;
            if (straightTrimCenterElapsed >= STRAIGHT_TRIM_CENTER_MS) {
              straightTrimPending = 0;
              straightTrimCenterPending = 0;
              straightTrimSlow = 0;
            }
          } else {
            straightElapsed = straightElapsed + straightDelta;
            if (straightElapsed >= STRAIGHT_STAGE4_MS) {
              straightPwm = SPEED_STRAIGHT;
            } else if (straightElapsed >= STRAIGHT_STAGE3_MS) {
              straightPwm = STRAIGHT_STAGE3_PWM;
            } else if (straightElapsed >= STRAIGHT_STAGE2_MS) {
              straightPwm = STRAIGHT_STAGE2_PWM;
            } else {
              straightPwm = STRAIGHT_STAGE1_PWM;
            }
            if (straightPwm >= SPEED_STRAIGHT) {
              straightPwm = SPEED_STRAIGHT;
            }
          }
        } else if (sensorF == 6 || sensorF == 12) {
          if (straightPending == 1) {
            if (straightTrimPending == 0) {
              straightTrimPending = 1;
              straightTrimAt = turnNow;
            }
            straightTrimCenterPending = 0;
            straightTrimElapsed = turnNow - straightTrimAt;
            if (straightTrimElapsed < STRAIGHT_TRIM_MAX_MS) {
              straightTrimAllowed = 1;
            } else {
              straightTrimAllowed = 0;
              straightTrimSlow = 1;
            }
          } else {
            straightPending = 0;
            straightElapsed = 0;
            straightPwm = STRAIGHT_STAGE1_PWM;
            straightTrimPending = 0;
            straightTrimCenterPending = 0;
            straightTrimAllowed = 0;
            straightTrimSlow = 0;
          }
        } else {
          straightPending = 0;
          straightElapsed = 0;
          straightPwm = STRAIGHT_STAGE1_PWM;
          straightTrimPending = 0;
          straightTrimCenterPending = 0;
          straightTrimAllowed = 0;
          straightTrimSlow = 0;
        }
      }
    } else {
      straightPending = 0;
      straightElapsed = 0;
      straightPwm = STRAIGHT_STAGE1_PWM;
      straightTrimPending = 0;
      straightTrimCenterPending = 0;
      straightTrimAllowed = 0;
      straightTrimSlow = 0;
    }
    straightTrimInner = straightPwm - STRAIGHT_TRIM_PWM;
    if (straightTrimInner < SPEED_TURN_INNER_MEDIUM) {
      straightTrimInner = SPEED_TURN_INNER_MEDIUM;
    }
    if (LIFT_ENABLED == 1) {
      if (LIFT_CROSSING_INDEX <= 0) {
        turnFault = 1;
      }
      if (lapReady == 1 && liftState == 0 && turnActive == 0 && gapActive == 0 && turnFault == 0 && lapDone == 0) {
        if (sensorF == 14) {
          liftClearPending = 0;
          if (liftMarkerLatched == 0) {
            if (liftMarkerPending == 0) {
              liftMarkerPending = 1;
              liftMarkerAt = turnNow;
            }
            liftMarkerElapsed = turnNow - liftMarkerAt;
            if (liftMarkerElapsed >= LIFT_MARKER_CONFIRM_MS) {
              liftMarkerLatched = 1;
              liftMarkerArmed = 1;
              liftMarkerPending = 0;
            }
          }
        } else {
          if (liftMarkerArmed == 1 && sensorF == 4 && outerCandidate == 0 && outerReady == 0) {
            liftCrossings = liftCrossings + 1;
            if (liftCrossings == LIFT_CROSSING_INDEX) {
              liftState = 1;
              liftWaitAt = turnNow;
              liftExitPending = 0;
              turnDirection = 0;
              turnCandidate = 0;
              wideActive = 0;
            }
          }
          liftMarkerArmed = 0;
          liftMarkerPending = 0;
        }
      } else {
        liftMarkerPending = 0;
        liftMarkerArmed = 0;
      }
      if (sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12) {
        if (liftClearPending == 0) {
          liftClearPending = 1;
          liftClearAt = turnNow;
        }
        liftClearElapsed = turnNow - liftClearAt;
        if (liftClearElapsed >= LIFT_CLEAR_CONFIRM_MS) {
          liftMarkerLatched = 0;
        }
      } else {
        liftClearPending = 0;
      }
    }
    if (lapStarted == 0) {
      lapStarted = 1;
      lapAt = turnNow;
    }
    lapElapsed = turnNow - lapAt;
    if (lapElapsed >= MAX_LAP_MS) {
      turnFault = 1;
    }
    if (lapReady == 0) {
      if (sensorF == 2 || sensorF == 4 || sensorF == 6 || sensorF == 8 || sensorF == 12) {
        if (departPending == 0) {
          departPending = 1;
          departAt = turnNow;
        }
        departElapsed = turnNow - departAt;
        if (departElapsed >= DEPART_CONFIRM_MS) {
          lapReady = 1;
        }
      } else {
        departPending = 0;
      }
    }
    if ((liftState == 0 || liftState == 3) && sensorF == 14 && turnActive == 0 && gapActive == 0) {
      if (wideActive == 0) {
        wideActive = 1;
        wideAt = turnNow;
      }
      wideElapsed = turnNow - wideAt;
      if (wideElapsed >= WIDE_TIMEOUT_MS) {
        turnFault = 1;
      } else if ((LIFT_ENABLED == 0 || liftState == 3) && lapReady == 1 && lapElapsed >= MIN_LAP_MS && wideElapsed >= FINISH_CONFIRM_MS) {
        lapDone = 1;
      }
    } else {
      wideActive = 0;
    }
    if ((liftState == 0 || liftState == 3) && turnActive == 0 && gapActive == 0 && turnFault == 0 && lapDone == 0) {
      if (sensorF == 8 || sensorF == 12) {
        if (turnCandidate == -1) {
        } else {
          turnCandidate = -1;
          turnCandidateAt = turnNow;
        }
        turnCandidateElapsed = turnNow - turnCandidateAt;
        if (turnCandidateElapsed >= TURN_DIRECTION_CONFIRM_MS) {
          turnDirection = -1;
          turnSeenAt = turnNow;
        }
      } else if (sensorF == 2 || sensorF == 6) {
        if (turnCandidate == 1) {
        } else {
          turnCandidate = 1;
          turnCandidateAt = turnNow;
        }
        turnCandidateElapsed = turnNow - turnCandidateAt;
        if (turnCandidateElapsed >= TURN_DIRECTION_CONFIRM_MS) {
          turnDirection = 1;
          turnSeenAt = turnNow;
        }
      } else if (sensorF == 0) {
        if (turnCandidate == -1 && turnDirection == 1 || turnCandidate == 1 && turnDirection == -1) {
          turnDirection = 0;
        }
        turnCandidate = 0;
      } else {
        turnCandidate = 0;
        if (sensorF == 14) {
          turnDirection = 0;
        }
      }
      if (sensorF == 4) {
        if (centerPending == 0) {
          centerPending = 1;
          centerAt = turnNow;
        }
        centerElapsed = turnNow - centerAt;
        if (centerElapsed >= TURN_CENTER_CLEAR_MS) {
          turnDirection = 0;
        }
      } else {
        centerPending = 0;
      }
      turnAge = turnNow - turnSeenAt;
      if (outerReady == 1 && outerDirection == 1 && sensorF == 2) {
        turnDirection = 1;
        turnDirectionSource = 1;
        turnActive = 1;
        turnAt = turnNow;
        turnConfirm = 0;
        outerProbeActive = 0;
        turnDeparted = 0;
        turnCaptureStarted = 0;
        turnCaptureGapPending = 0;
        turnCaptureSide = 1;
      } else if (outerReady == 1 && outerDirection == -1 && sensorF == 8) {
        turnDirection = -1;
        turnDirectionSource = 1;
        turnActive = 1;
        turnAt = turnNow;
        turnConfirm = 0;
        outerProbeActive = 0;
        turnDeparted = 0;
        turnCaptureStarted = 0;
        turnCaptureGapPending = 0;
        turnCaptureSide = -1;
      } else if (outerCandidate == 1 && sensorF == 2) {
        turnDirection = 1;
        turnDirectionSource = 0;
        turnActive = 1;
        turnAt = turnNow;
        turnConfirm = 0;
        outerProbeActive = 0;
        turnDeparted = 0;
        turnCaptureStarted = 0;
        turnCaptureGapPending = 0;
        turnCaptureSide = 1;
      } else if (outerCandidate == -1 && sensorF == 8) {
        turnDirection = -1;
        turnDirectionSource = 0;
        turnActive = 1;
        turnAt = turnNow;
        turnConfirm = 0;
        outerProbeActive = 0;
        turnDeparted = 0;
        turnCaptureStarted = 0;
        turnCaptureGapPending = 0;
        turnCaptureSide = -1;
      } else if (outerReady == 0 && outerCandidate == 0 && sensorF == 2 && turnCandidate == 1 && turnCandidateElapsed >= TURN_DIRECTION_CONFIRM_MS) {
        turnDirection = 1;
        turnDirectionSource = 0;
        turnActive = 1;
        turnAt = turnNow;
        turnConfirm = 0;
        outerProbeActive = 0;
        turnDeparted = 0;
        turnCaptureStarted = 0;
        turnCaptureGapPending = 0;
        turnCaptureSide = 1;
      } else if (outerReady == 0 && outerCandidate == 0 && sensorF == 8 && turnCandidate == -1 && turnCandidateElapsed >= TURN_DIRECTION_CONFIRM_MS) {
        turnDirection = -1;
        turnDirectionSource = 0;
        turnActive = 1;
        turnAt = turnNow;
        turnConfirm = 0;
        outerProbeActive = 0;
        turnDeparted = 0;
        turnCaptureStarted = 0;
        turnCaptureGapPending = 0;
        turnCaptureSide = -1;
      }
      if (sensorF == 0) {
        if (outerReady == 1) {
          turnDirection = outerDirection;
          turnDirectionSource = 1;
          turnActive = 1;
          turnAt = turnNow;
          turnConfirm = 0;
          outerProbeActive = 0;
          turnDeparted = 0;
          turnCaptureStarted = 0;
          turnCaptureGapPending = 0;
          turnCaptureSide = outerDirection;
        } else if (outerCandidate != 0) {
          if (outerProbeActive == 0) {
            outerProbeActive = 1;
            outerProbeAt = turnNow;
          }
          outerProbeElapsed = turnNow - outerProbeAt;
          if (outerProbeElapsed >= OUTER_PROBE_TIMEOUT_MS) {
            if (LOSS_STOP_ENABLED == 0 && sensorF == 0) {
              if (outerReady == 1) {
                gapDirection = outerDirection;
                gapDirectionAt = outerSeenAt;
              } else if (gapActive == 0 && turnActive == 1 && turnDirection != 0) {
                gapDirection = turnDirection;
                gapDirectionAt = turnNow;
              } else if (gapActive == 0 && turnDirection != 0 && turnAge <= TURN_MEMORY_MS) {
                gapDirection = turnDirection;
                gapDirectionAt = turnSeenAt;
              } else {
                if (gapActive == 0) {
                  gapDirection = 0;
                }
              }
              gapDirectionAge = turnNow - gapDirectionAt;
              turnActive = 0;
              turnDirection = 0;
              outerProbeActive = 0;
              gapActive = 1;
              gapAt = turnNow;
              gapConfirm = 0;
              whiteCount = 0;
              if (gapDirection == -1 && gapDirectionAge <= GAP_DIRECTION_MS) {
                digitalWrite(7,LOW);
                analogWrite(5,15);
                digitalWrite(4,HIGH);
                analogWrite(6,GAP_PWM);
              } else if (gapDirection == 1 && gapDirectionAge <= GAP_DIRECTION_MS) {
                digitalWrite(7,LOW);
                analogWrite(5,GAP_PWM);
                digitalWrite(4,HIGH);
                analogWrite(6,15);
              } else {
                digitalWrite(7,LOW);
                analogWrite(5,GAP_PWM);
                digitalWrite(4,HIGH);
                analogWrite(6,GAP_PWM);
              }
            } else {
              turnFault = 1;
            }
          }
        } else if (outerProbeActive == 1) {
          if (LOSS_STOP_ENABLED == 0 && sensorF == 0) {
            if (outerReady == 1) {
              gapDirection = outerDirection;
              gapDirectionAt = outerSeenAt;
            } else if (gapActive == 0 && turnActive == 1 && turnDirection != 0) {
              gapDirection = turnDirection;
              gapDirectionAt = turnNow;
            } else if (gapActive == 0 && turnDirection != 0 && turnAge <= TURN_MEMORY_MS) {
              gapDirection = turnDirection;
              gapDirectionAt = turnSeenAt;
            } else {
              if (gapActive == 0) {
                gapDirection = 0;
              }
            }
            gapDirectionAge = turnNow - gapDirectionAt;
            turnActive = 0;
            turnDirection = 0;
            outerProbeActive = 0;
            gapActive = 1;
            gapAt = turnNow;
            gapConfirm = 0;
            whiteCount = 0;
            if (gapDirection == -1 && gapDirectionAge <= GAP_DIRECTION_MS) {
              digitalWrite(7,LOW);
              analogWrite(5,15);
              digitalWrite(4,HIGH);
              analogWrite(6,GAP_PWM);
            } else if (gapDirection == 1 && gapDirectionAge <= GAP_DIRECTION_MS) {
              digitalWrite(7,LOW);
              analogWrite(5,GAP_PWM);
              digitalWrite(4,HIGH);
              analogWrite(6,15);
            } else {
              digitalWrite(7,LOW);
              analogWrite(5,GAP_PWM);
              digitalWrite(4,HIGH);
              analogWrite(6,GAP_PWM);
            }
          } else {
            turnFault = 1;
          }
        } else if (turnDirection != 0 && turnAge <= TURN_MEMORY_MS) {
          turnDirection = turnDirection;
          turnDirectionSource = 0;
          turnActive = 1;
          turnAt = turnNow;
          turnConfirm = 0;
          outerProbeActive = 0;
          turnDeparted = 0;
          turnCaptureStarted = 0;
          turnCaptureGapPending = 0;
          turnCaptureSide = turnDirection;
        } else {
          outerProbeActive = 0;
          gapActive = 1;
          gapDirection = 0;
          gapDirectionAt = turnNow;
          gapAt = turnNow;
          gapConfirm = 0;
        }
      }
    }
    if (turnFault == 1 || lapDone == 1) {
      stop2();
    } else if (LIFT_ENABLED == 1 && (liftState == 1 || liftState == 2)) {
      lift_control();
    } else if (splitActive == 1) {
      stop2();
    } else if (outerProbeActive == 1) {
      stop2();
    } else if (turnActive == 1) {
      sharp_turn();
    } else if (gapActive == 1) {
      cross_gap();
    } else if (wideActive == 1) {
      digitalWrite(7,LOW);
      analogWrite(5,WIDE_PWM);
      digitalWrite(4,HIGH);
      analogWrite(6,WIDE_PWM);
    } else {
      // Straight stages100/150/190/230 accumulate centered time only.
      // Brief F6/F12 trim keeps the current stage, outer wheel at stage
      // PWM and inner minus30, for a shared30ms event. Centered30ms
      // clears that event. Mild correction expiry uses curve output
      // without clearing stage; centered30ms restores retained stage.
      // Strong side/loss/confirmed outer resets stages. F10 is intercepted
      // by a20ms bounded zero-output confirmation; repeated blips share a
      // deadline until15ms valid line. Unexpected normal patterns stop.
      if (sensorF == 8) {
        digitalWrite(7,LOW);
        analogWrite(5,innerSpeed);
        digitalWrite(4,HIGH);
        analogWrite(6,SPEED_CURVE);
      } else if (sensorF == 2) {
        digitalWrite(7,LOW);
        analogWrite(5,SPEED_CURVE);
        digitalWrite(4,HIGH);
        analogWrite(6,innerSpeed);
      } else if (sensorF == 12) {
        if (straightTrimAllowed == 1) {
          digitalWrite(7,LOW);
          analogWrite(5,straightTrimInner);
          digitalWrite(4,HIGH);
          analogWrite(6,straightPwm);
        } else {
          digitalWrite(7,LOW);
          analogWrite(5,innerSpeed);
          digitalWrite(4,HIGH);
          analogWrite(6,SPEED_CURVE);
        }
      } else if (sensorF == 6) {
        if (straightTrimAllowed == 1) {
          digitalWrite(7,LOW);
          analogWrite(5,straightPwm);
          digitalWrite(4,HIGH);
          analogWrite(6,straightTrimInner);
        } else {
          digitalWrite(7,LOW);
          analogWrite(5,SPEED_CURVE);
          digitalWrite(4,HIGH);
          analogWrite(6,innerSpeed);
        }
      } else if (sensorF == 4) {
        if (straightWarning == 1) {
          digitalWrite(7,LOW);
          analogWrite(5,STRAIGHT_STAGE1_PWM);
          digitalWrite(4,HIGH);
          analogWrite(6,STRAIGHT_STAGE1_PWM);
        } else {
          if (straightTrimSlow == 1 && straightPwm >= SPEED_CURVE) {
            digitalWrite(7,LOW);
            analogWrite(5,SPEED_CURVE);
            digitalWrite(4,HIGH);
            analogWrite(6,SPEED_CURVE);
          } else {
            digitalWrite(7,LOW);
            analogWrite(5,straightPwm);
            digitalWrite(4,HIGH);
            analogWrite(6,straightPwm);
          }
        }
      } else {
        turnFault = 1;
        stop2();
      }
    }
    update_status_led();
    if (DEBUG_SERIAL == 1) {
      telemetryElapsed = turnNow - telemetryAt;
      if (telemetryElapsed >= TELEMETRY_PERIOD_MS) {
        telemetryAt = turnNow;
        // Original 115200-baud raw ADC/F telemetry; no new capture protocol.
        Serial.print((String("A1=") + String(rawA1)));
        Serial.print((String("A2=") + String(rawA2)));
        Serial.print((String("A3=") + String(rawA3)));
        Serial.print((String("A4=") + String(rawA4)));
        Serial.print((String("A5=") + String(rawA5)));
        Serial.println((String("F=") + String(sensorF)));
      }
    }
    if (sensorF > 0) {
      whiteCount = 0;
    }

}