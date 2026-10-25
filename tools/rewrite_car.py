"""Rebuild the active three-sensor CAGEBOT workspace from the preserved baseline.

This is a structural rewrite, not the temporal controller's build.py pipeline.
Export the resulting XML with the actual CAGEBOT Arduino generator.
"""
from copy import deepcopy
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from blockly_codegen import (Exporter, setv, cond, cases, call, eq, ge, le,
                             both, either, sub, add, anyof, lt, ne)
NS = 'https://developers.google.com/blockly/xml'
N = {'b': NS}
ET.register_namespace('', NS)
ET.register_namespace('html', 'http://www.w3.org/1999/xhtml')


def tag(name):
    return '{' + NS + '}' + name


def note(block, text):
    c = ET.SubElement(block, tag('comment'), pinned='false', h='100', w='380')
    c.text = text


def prune_chain(parent, name, remove):
    statement = parent.find("b:statement[@name='%s']" % name, N)
    first = statement.find('b:block', N)
    kept = []
    while first is not None:
        nxt = first.find('b:next', N)
        following = nxt.find('b:block', N) if nxt is not None else None
        if nxt is not None:
            first.remove(nxt)
        if first.get('id') not in remove and first.get('disabled') != 'true':
            kept.append(first)
        first = following
    statement.clear()
    statement.set('name', name)
    holder = statement
    for index, block in enumerate(kept):
        holder.append(block)
        if index < len(kept) - 1:
            holder = ET.SubElement(block, tag('next'))


def add_sharp_turns(root, main, decision):
    """Follow a departing edge into a bounded pivot until the center line returns."""
    exporter = Exporter()
    settings = {
        'SPEED_CURVE': ('int', 174),
        'TURN_OUTER_PWM': ('int', 150),
        'TURN_INNER_PWM': ('int', 114),
        'TURN_TIMEOUT_MS': ('unsigned long', 800),
        'TURN_MIN_MS': ('unsigned long', 30),
        'TURN_MEMORY_MS': ('unsigned long', 250),
        'TURN_CENTER_CLEAR_MS': ('unsigned long', 80),
        'TURN_DIRECTION_CONFIRM_MS': ('unsigned long', 15),
        'TURN_REACQUIRE_MS': ('unsigned long', 15),
        'turnDirection': ('int', 0),
        'turnActive': ('int', 0),
        'turnFault': ('int', 0),
        'OUTER_TURN_ASSIST': ('int', 1),
        'OUTER_LINE_THRESHOLD': ('int', 70),
        'OUTER_BACKGROUND_THRESHOLD': ('int', 120),
        'OUTER_CONFIRM_MS': ('unsigned long', 20),
        'OUTER_MEMORY_MS': ('unsigned long', 120),
        'OUTER_PROBE_TIMEOUT_MS': ('unsigned long', 80),
        'OUTER_OVERRIDE_WINDOW_MS': ('unsigned long', 150),
        'outerCandidate': ('int', 0),
        'outerCandidateAt': ('unsigned long', 0),
        'outerCandidateElapsed': ('unsigned long', 0),
        'outerDirection': ('int', 0),
        'outerSeenAt': ('unsigned long', 0),
        'outerAge': ('unsigned long', 0),
        'outerReady': ('int', 0),
        'outerProbeActive': ('int', 0),
        'outerProbeAt': ('unsigned long', 0),
        'outerProbeElapsed': ('unsigned long', 0),
        'turnDirectionSource': ('int', 0),
        'turnConfirm': ('int', 0),
        'turnCaptureAt': ('unsigned long', 0),
        'turnCaptureElapsed': ('unsigned long', 0),
        'turnNow': ('unsigned long', 0),
        'turnAt': ('unsigned long', 0),
        'turnSeenAt': ('unsigned long', 0),
        'turnElapsed': ('unsigned long', 0),
        'turnAge': ('unsigned long', 0),
        'centerPending': ('int', 0),
        'centerAt': ('unsigned long', 0),
        'centerElapsed': ('unsigned long', 0),
        'turnCandidate': ('int', 0),
        'turnCandidateAt': ('unsigned long', 0),
        'turnCandidateElapsed': ('unsigned long', 0),
        'GAP_PWM': ('int', 45),
        'GAP_TIMEOUT_MS': ('unsigned long', 120),
        'gapActive': ('int', 0),
        'gapAt': ('unsigned long', 0),
        'gapElapsed': ('unsigned long', 0),
        'gapConfirm': ('int', 0),
        'GAP_REACQUIRE_MS': ('unsigned long', 15),
        'gapCaptureAt': ('unsigned long', 0),
        'gapCaptureElapsed': ('unsigned long', 0),
        'DEBUG_SERIAL': ('int', 0),
        'TELEMETRY_PERIOD_MS': ('unsigned long', 50),
        'telemetryAt': ('unsigned long', 0),
        'telemetryElapsed': ('unsigned long', 0),
        'ledStatus': ('int', 1),
        'ledDesired': ('int', 1),
        'STRAIGHT_STAGE2_MS': ('unsigned long', 200),
        'STRAIGHT_STAGE3_MS': ('unsigned long', 500),
        'STRAIGHT_STAGE4_MS': ('unsigned long', 900),
        'STRAIGHT_STAGE2_PWM': ('int', 150),
        'STRAIGHT_STAGE3_PWM': ('int', 190),
        'STRAIGHT_STAGE1_PWM': ('int', 100),
        'STRAIGHT_TRIM_PWM': ('int', 30),
        'STRAIGHT_TRIM_MAX_MS': ('unsigned long', 30),
        'STRAIGHT_TRIM_CENTER_MS': ('unsigned long', 30),
        'straightPending': ('int', 0),
        'straightElapsed': ('unsigned long', 0),
        'straightLastAt': ('unsigned long', 0),
        'straightDelta': ('unsigned long', 0),
        'straightTrimPending': ('int', 0),
        'straightTrimAt': ('unsigned long', 0),
        'straightTrimElapsed': ('unsigned long', 0),
        'straightTrimCenterPending': ('int', 0),
        'straightTrimCenterAt': ('unsigned long', 0),
        'straightTrimCenterElapsed': ('unsigned long', 0),
        'straightTrimAllowed': ('int', 0),
        'straightTrimInner': ('int', 70),
        'straightPwm': ('int', 100),
        'MIN_LAP_MS': ('unsigned long', 15000),
        'MAX_LAP_MS': ('unsigned long', 180000),
        'DEPART_CONFIRM_MS': ('unsigned long', 100),
        'FINISH_CONFIRM_MS': ('unsigned long', 250),
        'WIDE_TIMEOUT_MS': ('unsigned long', 900),
        'WIDE_PWM': ('int', 45),
        'lapStarted': ('int', 0),
        'lapReady': ('int', 0),
        'lapDone': ('int', 0),
        'lapAt': ('unsigned long', 0),
        'lapElapsed': ('unsigned long', 0),
        'departPending': ('int', 0),
        'departAt': ('unsigned long', 0),
        'departElapsed': ('unsigned long', 0),
        'wideActive': ('int', 0),
        'wideAt': ('unsigned long', 0),
        'wideElapsed': ('unsigned long', 0),
        # User reports no earlier crossings; first confirmed wide marker is assumed.
        'LIFT_ENABLED': ('int', 1),
        'LIFT_CROSSING_INDEX': ('int', 1),
        'LIFT_MARKER_CONFIRM_MS': ('unsigned long', 30),
        'LIFT_CLEAR_CONFIRM_MS': ('unsigned long', 100),
        'LIFT_WAIT_MS': ('unsigned long', 23350),
        'LIFT_AUTO_EXIT': ('int', 1),
        'LIFT_EXIT_PWM': ('int', 45),
        'LIFT_EXIT_TIMEOUT_MS': ('unsigned long', 1500),
        'liftState': ('int', 0),
        'liftCrossings': ('int', 0),
        'liftMarkerLatched': ('int', 0),
        'liftMarkerPending': ('int', 0),
        'liftMarkerAt': ('unsigned long', 0),
        'liftMarkerElapsed': ('unsigned long', 0),
        'liftClearPending': ('int', 0),
        'liftClearAt': ('unsigned long', 0),
        'liftClearElapsed': ('unsigned long', 0),
        'liftWaitAt': ('unsigned long', 0),
        'liftWaitElapsed': ('unsigned long', 0),
        'liftExitAt': ('unsigned long', 0),
        'liftExitElapsed': ('unsigned long', 0),
        'liftExitPending': ('int', 0),
        'liftLineAt': ('unsigned long', 0),
        'liftLineElapsed': ('unsigned long', 0),
    }
    variables = root.find('b:variables', N)
    for name in settings:
        ET.SubElement(variables, tag('variable'), id='var_' + name).text = name
    setup = main.find("b:statement[@name='MySetup']", N)
    first = setup.find('b:block', N)
    setup.remove(first)
    declarations = exporter.chain([('declare', name, kind, value)
                                   for name, (kind, value) in settings.items()])
    last = declarations
    while last.find('b:next/b:block', N) is not None:
        last = last.find('b:next/b:block', N)
    ET.SubElement(last, tag('next')).append(first)
    setup.append(declarations)

    left = [('digitalwrite', '7', 1), ('pwm', '5', 'TURN_INNER_PWM'),
            ('digitalwrite', '4', 1), ('pwm', '6', 'TURN_OUTER_PWM')]
    right = [('digitalwrite', '7', 0), ('pwm', '5', 'TURN_OUTER_PWM'),
             ('digitalwrite', '4', 0), ('pwm', '6', 'TURN_INNER_PWM')]
    forward = [('digitalwrite', '7', 0), ('pwm', '5', 'SPEED_CURVE'),
               ('digitalwrite', '4', 1), ('pwm', '6', 'SPEED_CURVE')]
    capture_drive = [cases([
        (eq('sensorF', 12), [('digitalwrite', '7', 0), ('pwm', '5', 'innerSpeed'),
                            ('digitalwrite', '4', 1), ('pwm', '6', 'SPEED_CURVE')]),
        (eq('sensorF', 6), [('digitalwrite', '7', 0), ('pwm', '5', 'SPEED_CURVE'),
                           ('digitalwrite', '4', 1), ('pwm', '6', 'innerSpeed')])], forward)]
    done = [setv('turnActive', 0), setv('turnDirection', 0),
            setv('turnConfirm', 0), setv('whiteCount', 0)] + capture_drive
    # Deadline is fixed at entry and has priority over reacquisition.
    pivot = [setv('turnElapsed', sub('turnNow', 'turnAt')),
             cond(both(eq('turnDirectionSource', 0),
                       both(le('turnElapsed', 'OUTER_OVERRIDE_WINDOW_MS'), eq('outerReady', 1))), [
                 setv('turnDirection', 'outerDirection'), setv('turnDirectionSource', 1)]),
             cond(either(ge('turnElapsed', 'TURN_TIMEOUT_MS'),
                         both(eq('OUTER_TURN_ASSIST', 1),
                              both(eq('turnDirectionSource', 0),
                                   ge('turnElapsed', 'OUTER_OVERRIDE_WINDOW_MS')))),
                  [setv('turnFault', 1), setv('turnActive', 0), call('stop')], [
                 cond(both(ge('turnElapsed', 'TURN_MIN_MS'), anyof('sensorF', [4, 6, 12])),
                      [cond(eq('turnConfirm', 0), [
                          setv('turnConfirm', 1), setv('turnCaptureAt', 'turnNow')]),
                       setv('turnCaptureElapsed', sub('turnNow', 'turnCaptureAt'))],
                      [setv('turnConfirm', 0)]),
                 cond(both(eq('turnConfirm', 1), ge('turnCaptureElapsed', 'TURN_REACQUIRE_MS')), done, [
                     cond(ge('turnConfirm', 1), capture_drive,
                          [cond(eq('turnDirection', -1), left, right)])])])]
    function = exporter.block('procedures_defnoreturn')
    function.set('x', '900')
    function.set('y', '0')
    exporter.field(function, 'NAME', 'sharp_turn')
    exporter.field(function, 'TYPE', 'void')
    exporter.statement(function, 'STACK', pivot)
    note(function, 'A1=right/A5=left outer assistance. Center-only search gets at most150ms to capture line or receive confirmed outer support; otherwise stop. Outer evidence may correct it once without resetting the800ms total deadline. Confirmed outer plus matching F2/F8 starts before full loss. Outer forward150/inner reverse114; continuous15ms capture finishes at base174.')
    root.append(function)

    # A short gap has its own fixed deadline and never inherits a pivot command.
    gap_drive = [('digitalwrite', '7', 0), ('pwm', '5', 'GAP_PWM'),
                 ('digitalwrite', '4', 1), ('pwm', '6', 'GAP_PWM')]
    def gap_wheels(left_pwm, right_pwm):
        return [('digitalwrite', '7', 0), ('pwm', '5', left_pwm),
                ('digitalwrite', '4', 1), ('pwm', '6', right_pwm)]
    gap_capture = [cases([
        (eq('sensorF', 8), gap_wheels(20, 'GAP_PWM')),
        (eq('sensorF', 12), gap_wheels(30, 'GAP_PWM')),
        (eq('sensorF', 2), gap_wheels('GAP_PWM', 20)),
        (eq('sensorF', 6), gap_wheels('GAP_PWM', 30))], gap_drive)]
    gap = [setv('gapElapsed', sub('turnNow', 'gapAt')),
           cond(ge('gapElapsed', 'GAP_TIMEOUT_MS'),
                [setv('turnFault', 1), setv('gapActive', 0), call('stop')], [
               cond(anyof('sensorF', [2, 4, 6, 8, 12]),
                    [cond(eq('gapConfirm', 0), [
                        setv('gapConfirm', 1), setv('gapCaptureAt', 'turnNow')]),
                     setv('gapCaptureElapsed', sub('turnNow', 'gapCaptureAt'))],
                    [setv('gapConfirm', 0)]),
               cond(either(both(eq('gapConfirm', 1), ge('gapCaptureElapsed', 'GAP_REACQUIRE_MS')),
                           eq('sensorF', 14)),
                    [setv('gapActive', 0), setv('turnDirection', 0),
                     setv('whiteCount', 0)] + gap_capture, gap_capture)])]
    function = exporter.block('procedures_defnoreturn')
    function.set('x', '900')
    function.set('y', '650')
    exporter.field(function, 'NAME', 'cross_gap')
    exporter.field(function, 'TYPE', 'void')
    exporter.statement(function, 'STACK', gap)
    note(function, 'Short gap PWM45 with fixed120ms deadline. Side-line return starts differential capture20/45 or30/45 immediately. Continuous narrow line15ms finishes; invalid observations reset confirmation, not the event deadline. Wide line returns to marker handling.')
    root.append(function)

    wide_drive = [('digitalwrite', '7', 0), ('pwm', '5', 'WIDE_PWM'),
                  ('digitalwrite', '4', 1), ('pwm', '6', 'WIDE_PWM')]
    narrow = anyof('sensorF', [2, 4, 6, 8, 12])
    normal_lift_state = either(eq('liftState', 0), eq('liftState', 3))
    lift_update = [cond(eq('LIFT_ENABLED', 1), [
        cond(le('LIFT_CROSSING_INDEX', 0), [setv('turnFault', 1)]),
        cond(both(eq('lapReady', 1),
                  both(normal_lift_state, both(eq('turnActive', 0), eq('gapActive', 0)))), [
            cond(eq('sensorF', 14), [
                setv('liftClearPending', 0),
                cond(eq('liftMarkerLatched', 0), [
                    cond(eq('liftMarkerPending', 0), [
                        setv('liftMarkerPending', 1), setv('liftMarkerAt', 'turnNow')]),
                    setv('liftMarkerElapsed', sub('turnNow', 'liftMarkerAt')),
                    cond(ge('liftMarkerElapsed', 'LIFT_MARKER_CONFIRM_MS'), [
                        setv('liftMarkerLatched', 1), setv('liftMarkerPending', 0),
                        setv('liftCrossings', add('liftCrossings', 1)),
                        cond(both(eq('liftState', 0), eq('liftCrossings', 'LIFT_CROSSING_INDEX')), [
                            setv('liftState', 1), setv('liftWaitAt', 'turnNow'),
                            setv('liftExitPending', 0), setv('turnDirection', 0),
                            setv('turnCandidate', 0), setv('wideActive', 0)])])])], [
                setv('liftMarkerPending', 0)])], [setv('liftMarkerPending', 0)]),
        # A marker is consumed until stable narrow line, including during exit.
        cond(narrow, [
            cond(eq('liftClearPending', 0), [
                setv('liftClearPending', 1), setv('liftClearAt', 'turnNow')]),
            setv('liftClearElapsed', sub('turnNow', 'liftClearAt')),
            cond(ge('liftClearElapsed', 'LIFT_CLEAR_CONFIRM_MS'),
                 [setv('liftMarkerLatched', 0)])], [setv('liftClearPending', 0)])])]
    exit_drive = [('digitalwrite', '7', 0), ('pwm', '5', 'LIFT_EXIT_PWM'),
                  ('digitalwrite', '4', 1), ('pwm', '6', 'LIFT_EXIT_PWM')]
    lift_control = [cases([
        (eq('liftState', 1), [
            call('stop'), setv('liftWaitElapsed', sub('turnNow', 'liftWaitAt')),
            cond(both(eq('LIFT_AUTO_EXIT', 1), ge('liftWaitElapsed', 'LIFT_WAIT_MS')), [
                setv('liftState', 2), setv('liftExitAt', 'turnNow'),
                setv('liftExitPending', 0)])]),
        (eq('liftState', 2), [
            setv('liftExitElapsed', sub('turnNow', 'liftExitAt')),
            cond(ge('liftExitElapsed', 'LIFT_EXIT_TIMEOUT_MS'),
                 [setv('turnFault', 1), call('stop')], [
                cond(narrow, [
                    cond(eq('liftExitPending', 0), [
                        setv('liftExitPending', 1), setv('liftLineAt', 'turnNow')]),
                    setv('liftLineElapsed', sub('turnNow', 'liftLineAt')),
                    cond(ge('liftLineElapsed', 'LIFT_CLEAR_CONFIRM_MS'), [
                        setv('liftState', 3), setv('turnDirection', 0),
                        setv('turnCandidate', 0), setv('centerPending', 0),
                        setv('wideActive', 0), setv('whiteCount', 0)])],
                    [setv('liftExitPending', 0)]),
                *exit_drive])])])]
    function = exporter.block('procedures_defnoreturn')
    function.set('x', '1650')
    function.set('y', '650')
    exporter.field(function, 'NAME', 'lift_control')
    exporter.field(function, 'TYPE', 'void')
    exporter.statement(function, 'STACK', lift_control)
    note(function, 'Lift: first confirmed wide marker after narrow-line departure, based on user route assumption. Stop without alignment drive; user-requested wait23350ms from stop command, not measured settled feedback. This is below the published27s +/-5% timing. Auto exit PWM45 with1500ms limit. Consume marker once. PWM zero is not active braking. Disable LIFT_ENABLED for the earlier practice mat without a lift.')
    root.append(function)
    lap_update = [
        cond(eq('lapStarted', 0), [setv('lapStarted', 1), setv('lapAt', 'turnNow')]),
        setv('lapElapsed', sub('turnNow', 'lapAt')),
        cond(ge('lapElapsed', 'MAX_LAP_MS'), [setv('turnFault', 1)]),
        cond(eq('lapReady', 0), [
            cond(anyof('sensorF', [2, 4, 6, 8, 12]), [
                cond(eq('departPending', 0),
                     [setv('departPending', 1), setv('departAt', 'turnNow')]),
                setv('departElapsed', sub('turnNow', 'departAt')),
                cond(ge('departElapsed', 'DEPART_CONFIRM_MS'), [setv('lapReady', 1)])],
                [setv('departPending', 0)])]),
        cond(both(normal_lift_state,
                  both(eq('sensorF', 14), both(eq('turnActive', 0), eq('gapActive', 0)))), [
            cond(eq('wideActive', 0), [setv('wideActive', 1), setv('wideAt', 'turnNow')]),
            setv('wideElapsed', sub('turnNow', 'wideAt')),
            # The event timeout remains fixed even across the minimum-lap threshold.
            cases([(ge('wideElapsed', 'WIDE_TIMEOUT_MS'), [setv('turnFault', 1)]),
                   (both(either(eq('LIFT_ENABLED', 0), eq('liftState', 3)),
                         both(eq('lapReady', 1), both(ge('lapElapsed', 'MIN_LAP_MS'),
                                                ge('wideElapsed', 'FINISH_CONFIRM_MS')))),
                    [setv('lapDone', 1)])])], [setv('wideActive', 0)])]
    def candidate_direction(direction):
        return [
            cond(eq('turnCandidate', direction), [],
                 [setv('turnCandidate', direction), setv('turnCandidateAt', 'turnNow')]),
            setv('turnCandidateElapsed', sub('turnNow', 'turnCandidateAt')),
            cond(ge('turnCandidateElapsed', 'TURN_DIRECTION_CONFIRM_MS'),
                 [setv('turnDirection', direction), setv('turnSeenAt', 'turnNow')])]
    def outer_candidate(direction):
        return [cond(ne('outerCandidate', direction), [
                    setv('outerCandidate', direction), setv('outerCandidateAt', 'turnNow')]),
                setv('outerCandidateElapsed', sub('turnNow', 'outerCandidateAt')),
                cond(ge('outerCandidateElapsed', 'OUTER_CONFIRM_MS'), [
                    setv('outerDirection', direction), setv('outerSeenAt', 'turnNow')])]
    outer_update = [
        cond(ne('sensorF', 0), [setv('outerProbeActive', 0)]),
        cond(both(eq('OUTER_TURN_ASSIST', 1), anyof('sensorF', [0, 2, 4, 6, 8, 12])), [
            cases([
                (both(lt('rawA1', 'OUTER_LINE_THRESHOLD'), ge('rawA5', 'OUTER_BACKGROUND_THRESHOLD')),
                 outer_candidate(1)),
                (both(lt('rawA5', 'OUTER_LINE_THRESHOLD'), ge('rawA1', 'OUTER_BACKGROUND_THRESHOLD')),
                 outer_candidate(-1))], [setv('outerCandidate', 0)]),
            cond(both(lt('rawA1', 'OUTER_LINE_THRESHOLD'), lt('rawA5', 'OUTER_LINE_THRESHOLD')),
                 [setv('outerDirection', 0)])],
             [setv('outerCandidate', 0), setv('outerDirection', 0)]),
        setv('outerAge', sub('turnNow', 'outerSeenAt')), setv('outerReady', 0),
        cond(both(eq('OUTER_TURN_ASSIST', 1),
                  both(ne('outerDirection', 0), both(le('outerAge', 'OUTER_MEMORY_MS'),
                       either(eq('outerCandidate', 0), eq('outerCandidate', 'outerDirection'))))),
             [setv('outerReady', 1)])]
    def begin_turn(direction, source):
        return [setv('turnDirection', direction), setv('turnDirectionSource', source),
                setv('turnActive', 1), setv('turnAt', 'turnNow'),
                setv('turnConfirm', 0), setv('outerProbeActive', 0)]
    reset_straight = [setv('straightPending', 0), setv('straightElapsed', 0),
                      setv('straightPwm', 'STRAIGHT_STAGE1_PWM'),
                      setv('straightTrimPending', 0), setv('straightTrimCenterPending', 0),
                      setv('straightTrimAllowed', 0)]
    select_stage = [cases([
        (ge('straightElapsed', 'STRAIGHT_STAGE4_MS'), [setv('straightPwm', 'SPEED_STRAIGHT')]),
        (ge('straightElapsed', 'STRAIGHT_STAGE3_MS'), [setv('straightPwm', 'STRAIGHT_STAGE3_PWM')]),
        (ge('straightElapsed', 'STRAIGHT_STAGE2_MS'), [setv('straightPwm', 'STRAIGHT_STAGE2_PWM')])],
        [setv('straightPwm', 'STRAIGHT_STAGE1_PWM')]),
        cond(ge('straightPwm', 'SPEED_STRAIGHT'), [setv('straightPwm', 'SPEED_STRAIGHT')])]
    centered = [
        cond(eq('straightPending', 0), [setv('straightPending', 1),
             setv('straightElapsed', 0), setv('straightDelta', 0),
             setv('straightPwm', 'STRAIGHT_STAGE1_PWM')]),
        cond(eq('straightTrimPending', 1), [
            cond(eq('straightTrimCenterPending', 0), [setv('straightTrimCenterPending', 1),
                 setv('straightTrimCenterAt', 'turnNow')]),
            setv('straightTrimCenterElapsed', sub('turnNow', 'straightTrimCenterAt')),
            setv('straightTrimElapsed', sub('turnNow', 'straightTrimAt')),
            cases([(ge('straightTrimCenterElapsed', 'STRAIGHT_TRIM_CENTER_MS'),
                    [setv('straightTrimPending', 0), setv('straightTrimCenterPending', 0)]),
                   (ge('straightTrimElapsed', add('STRAIGHT_TRIM_MAX_MS', 'STRAIGHT_TRIM_CENTER_MS')), reset_straight)])],
            [setv('straightElapsed', add('straightElapsed', 'straightDelta'))] + select_stage)]
    mild = [cond(eq('straightPending', 1), [
        cond(eq('straightTrimPending', 0), [setv('straightTrimPending', 1),
             setv('straightTrimAt', 'turnNow')]),
        setv('straightTrimCenterPending', 0),
        setv('straightTrimElapsed', sub('turnNow', 'straightTrimAt')),
        cond(lt('straightTrimElapsed', 'STRAIGHT_TRIM_MAX_MS'),
             [setv('straightTrimAllowed', 1)], reset_straight)], reset_straight)]
    straight_update = [setv('straightDelta', sub('turnNow', 'straightLastAt')),
        setv('straightLastAt', 'turnNow'), setv('straightTrimAllowed', 0),
        cond(both(both(eq('outerCandidate', 0), eq('outerReady', 0)),
                  both(normal_lift_state, both(eq('turnActive', 0), both(eq('gapActive', 0),
                       both(eq('turnFault', 0), eq('lapDone', 0)))))), [
            cases([(eq('sensorF', 4), centered), (anyof('sensorF', [6, 12]), mild)], reset_straight)],
            reset_straight),
        setv('straightTrimInner', sub('straightPwm', 'STRAIGHT_TRIM_PWM')),
        cond(lt('straightTrimInner', 'SPEED_TURN_INNER_MEDIUM'),
             [setv('straightTrimInner', 'SPEED_TURN_INNER_MEDIUM')])]
    before = [setv('turnNow', ('millis',)),
              *outer_update,
              *straight_update,
              *lift_update,
              *lap_update,
              cond(both(normal_lift_state,
                    both(eq('turnActive', 0), both(eq('gapActive', 0),
                    both(eq('turnFault', 0), eq('lapDone', 0))))), [
                  cases([(either(eq('sensorF', 8), eq('sensorF', 12)),
                          candidate_direction(-1)),
                         (either(eq('sensorF', 2), eq('sensorF', 6)),
                          candidate_direction(1)),
                         (eq('sensorF', 0), [
                             # A new conflicting side is not evidence for the old turn.
                             cond(either(
                                 both(eq('turnCandidate', -1), eq('turnDirection', 1)),
                                 both(eq('turnCandidate', 1), eq('turnDirection', -1))),
                                  [setv('turnDirection', 0)]),
                             setv('turnCandidate', 0)])],
                        [setv('turnCandidate', 0),
                         cond(eq('sensorF', 14), [setv('turnDirection', 0)])]),
                  # A brief center observation must not erase an approaching corner.
                  # Sustained centered travel still clears stale direction for gaps.
                  cond(eq('sensorF', 4), [
                      cond(eq('centerPending', 0),
                           [setv('centerPending', 1), setv('centerAt', 'turnNow')]),
                      setv('centerElapsed', sub('turnNow', 'centerAt')),
                      cond(ge('centerElapsed', 'TURN_CENTER_CLEAR_MS'),
                           [setv('turnDirection', 0)])], [setv('centerPending', 0)]),
                  setv('turnAge', sub('turnNow', 'turnSeenAt')),
                  # Confirmed outer and matching single center-edge start before full loss.
                  cases([
                      (both(eq('outerReady', 1), both(eq('outerDirection', 1), eq('sensorF', 2))),
                       begin_turn(1, 1)),
                      (both(eq('outerReady', 1), both(eq('outerDirection', -1), eq('sensorF', 8))),
                       begin_turn(-1, 1))]),
                  cond(eq('sensorF', 0), [cases([
                      (eq('outerReady', 1), begin_turn('outerDirection', 1)),
                      (ne('outerCandidate', 0), [
                          cond(eq('outerProbeActive', 0), [
                              setv('outerProbeActive', 1), setv('outerProbeAt', 'turnNow')]),
                          setv('outerProbeElapsed', sub('turnNow', 'outerProbeAt')),
                          cond(ge('outerProbeElapsed', 'OUTER_PROBE_TIMEOUT_MS'),
                               [setv('turnFault', 1)])]),
                      (eq('outerProbeActive', 1), [setv('turnFault', 1)]),
                      (both(ne('turnDirection', 0), le('turnAge', 'TURN_MEMORY_MS')),
                       begin_turn('turnDirection', 0))], [
                          setv('outerProbeActive', 0), setv('gapActive', 1),
                          setv('gapAt', 'turnNow'), setv('gapConfirm', 0)])])])]
    head = exporter.chain(before)
    last = head
    while last.find('b:next/b:block', N) is not None:
        last = last.find('b:next/b:block', N)
    wrapper = exporter.stmt(cases([
        (either(eq('turnFault', 1), eq('lapDone', 1)), [call('stop')]),
        (both(eq('LIFT_ENABLED', 1), either(eq('liftState', 1), eq('liftState', 2))),
         [call('lift_control')]),
        (eq('outerProbeActive', 1), [call('stop')]),
        (eq('turnActive', 1), [call('sharp_turn')]),
        (eq('gapActive', 1), [call('cross_gap')]),
        (eq('wideActive', 1), wide_drive)], []))
    blue = next(b for b in main.findall('.//b:block', N)
                if b.get('type') == 'ws2812_color'
                and any(f.text == '#0000ff' for f in b.findall('.//b:field', N)))
    blue = deepcopy(blue)
    blue_next = blue.find('b:next', N)
    if blue_next is not None:
        blue.remove(blue_next)
    # The cloned LED value blocks need independent workspace IDs.
    for index, b in enumerate(blue.iter()):
        if b.get('id'):
            b.set('id', 'lap_stop_led_' + str(index))
    stop_call = wrapper.find("b:statement[@name='DO0']/b:block", N)
    ET.SubElement(stop_call, tag('next')).append(blue)
    ET.SubElement(last, tag('next')).append(wrapper)
    parent = next(p for p in main.iter() if decision in list(p))
    following = decision.find('b:next', N)
    if following is not None:
        decision.remove(following)
        wrapper.append(following)
    parent.remove(decision)
    wrapper.find("b:statement[@name='ELSE']", N).append(decision)
    parent.append(head)
    # Reuse existing variable IDs instead of creating duplicate vendor variables.
    ids = {v.text: v.get('id') for v in variables}
    for field in root.findall('.//b:field', N):
        if field.get('name') == 'VAR':
            field.set('id', ids[field.text])


def replace_normal_follow(main):
    """Only an explicitly centered observation may request straight speed."""
    exporter = Exporter()
    exporter.seq = 200000
    def wheels(left, right):
        return [('digitalwrite', '7', 0), ('pwm', '5', left),
                ('digitalwrite', '4', 1), ('pwm', '6', right)]
    # No empty Error branch and no unclassified default-forward branch.
    decision = main.find(".//b:block[@id='car_decision']", N)
    parent = next(p for p in main.iter() if decision in list(p))
    normal = exporter.stmt(cases([
        (eq('sensorF', 8), wheels('innerSpeed', 'SPEED_CURVE')),
        (eq('sensorF', 2), wheels('SPEED_CURVE', 'innerSpeed')),
        (eq('sensorF', 12), [cond(eq('straightTrimAllowed', 1),
             wheels('straightTrimInner', 'straightPwm'), wheels('innerSpeed', 'SPEED_CURVE'))]),
        (eq('sensorF', 6), [cond(eq('straightTrimAllowed', 1),
             wheels('straightPwm', 'straightTrimInner'), wheels('SPEED_CURVE', 'innerSpeed'))]),
        (eq('sensorF', 4), wheels('straightPwm', 'straightPwm'))],
        [setv('turnFault', 1), call('stop')]))
    note(normal, 'Straight stages100/150/190/230 accumulate centered time only. Brief F6/F12 trim keeps the current stage, outer wheel at stage PWM and inner minus30, for a shared30ms event. Centered30ms clears that event. Strong side/loss/outer warning resets stages. F10/unexpected patterns stop.')
    parent.remove(decision)
    parent.append(normal)


def streamline_loop_io(root, main):
    """Keep LED writes and optional telemetry outside the per-sample hot path."""
    exporter = Exporter()
    exporter.seq = 100000
    setup = main.find("b:statement[@name='MySetup']", N)
    loop = main.find("b:statement[@name='MyLoop']", N)
    def led_copy(color):
        original = next(b for b in setup.findall('.//b:block', N)
                        if b.get('type') == 'ws2812_color'
                        and any(f.text == color for f in b.findall(
                            "b:value[@name='RGBLED_COLOR']//b:field", N)))
        result = deepcopy(original)
        nxt = result.find('b:next', N)
        if nxt is not None:
            result.remove(nxt)
        for b in result.iter():
            if b.get('id'):
                exporter.seq += 1
                b.set('id', 'io_' + str(exporter.seq))
        return result
    green, blue = led_copy('#33ff33'), led_copy('#0000ff')
    # Preserve the boot LED, but remove all repeated runtime LED writes.
    for parent in list(loop.iter()):
        for child in list(parent):
            if child.get('type') == 'ws2812_color':
                following = child.find('b:next/b:block', N)
                parent.remove(child)
                if following is not None:
                    parent.append(following)
    body = [setv('ledDesired', 1),
            cond(either(eq('outerProbeActive', 1),
                        either(eq('turnFault', 1), either(eq('lapDone', 1), eq('liftState', 1)))),
                 [setv('ledDesired', 2)]),
            cond(eq('ledDesired', 'ledStatus'), [], [
                cond(eq('ledDesired', 2), [], []), setv('ledStatus', 'ledDesired')])]
    function = exporter.block('procedures_defnoreturn')
    function.set('x', '1650')
    function.set('y', '1300')
    exporter.field(function, 'NAME', 'update_status_led')
    exporter.field(function, 'TYPE', 'void')
    exporter.statement(function, 'STACK', body)
    selector = next(b for b in function.findall('.//b:block', N)
                    if b.get('type') == 'controls_if'
                    and b.find("b:statement[@name='ELSE']", N) is not None
                    and b.find("b:statement[@name='DO0']/b:block", N) is None)
    # This is the ledDesired==ledStatus guard; its ELSE contains the color selector.
    selector = selector.find("b:statement[@name='ELSE']/b:block", N)
    selector.find("b:statement[@name='DO0']", N).append(blue)
    selector.find("b:statement[@name='ELSE']", N).append(green)
    note(function, 'LED updates only on changes. Green=running; blue=outer-direction probe stop, lift wait, fault or finish. No per-loop NeoPixel show.')
    root.append(function)

    serial = main.find(".//b:block[@id='n0210']", N)
    parent = next(p for p in loop.iter() if serial in list(p))
    last = serial
    while last.find('b:next/b:block', N) is not None:
        following = last.find('b:next/b:block', N)
        if following.get('type') not in ('serial_print', 'serial_printL'):
            break
        last = following
    tail = last.find('b:next', N)
    if tail is not None:
        last.remove(tail)
    parent.remove(serial)
    periodic = exporter.stmt(cond(ge('telemetryElapsed', 'TELEMETRY_PERIOD_MS'),
                                  [setv('telemetryAt', 'turnNow')]))
    assignment = periodic.find("b:statement[@name='DO0']/b:block", N)
    ET.SubElement(assignment, tag('next')).append(serial)
    head = exporter.chain([call('update_status_led'), cond(eq('DEBUG_SERIAL', 1),
                          [setv('telemetryElapsed', sub('turnNow', 'telemetryAt'))])])
    debug = head.find('b:next/b:block', N)
    elapsed = debug.find("b:statement[@name='DO0']/b:block", N)
    ET.SubElement(elapsed, tag('next')).append(periodic)
    if tail is not None:
        debug.append(tail)
    parent.append(head)


def rewrite():
    root = ET.fromstring((ROOT / 'legacy/three_sensor_baseline/three_sensor_baseline.xml').read_text(encoding='utf-8'))
    main = root.find("b:block[@type='arduino_setup']", N)
    unused = {'SPEED_BACKWARD', 'SPEED_TURN_INNER_FINE', 'SPEED_TURN_PIVOT',
              'CROSS_HOLD', 'crossCount', 'dist'}
    setup_remove = {
        b.get('id') for b in main.findall('.//b:block', N)
        if b.get('type') == 'variables_declare'
        and b.find("b:field[@name='VAR']", N).text in unused
    }
    prune_chain(main, 'MySetup', setup_remove)
    # Straight speed is independent of the curve base and sharp-turn outputs.
    for block in main.findall(".//b:block[@type='variables_declare']", N):
        name = block.find("b:field[@name='VAR']", N).text
        parameters = {'SPEED_STRAIGHT': 230, 'TURN_KP': 174,
                      'SPEED_TURN_INNER_MEDIUM': 15}
        if name in parameters:
            block.find(".//b:field[@name='NUM']", N).text = str(parameters[name])
    # Outer ADCs stay available as raw telemetry but never enter F or sumW.
    prune_chain(main, 'MyLoop', {'n7018', 'n7050', 'sm0016', 'sm0060'})
    calculation = main.find(".//b:block[@id='sm0082']", N)
    # Restrict replacement to the arithmetic body, not its following blocks.
    for field in calculation.find("b:statement[@name='DO0']", N).findall('.//b:field', N):
        if field.get('name') == 'VAR' and field.text == 'SPEED_STRAIGHT':
            field.text = 'SPEED_CURVE'
    decision = main.find(".//b:block[@id='n7142']", N)
    old = {child.get('name'): deepcopy(child) for child in decision
           if child.tag in (tag('value'), tag('statement'))}
    tail = decision.find('b:next', N)
    if tail is not None:
        decision.remove(tail)
    decision.clear()
    decision.set('type', 'controls_if')
    decision.set('id', 'car_decision')
    ET.SubElement(decision, tag('mutation'), elseif='3', **{'else': '1'})
    # F=10 holds the previous command; then the original strict ADC turn checks.
    v = ET.SubElement(decision, tag('value'), name='IF0')
    eq = ET.SubElement(v, tag('block'), type='logic_compare', id='car_error_eq')
    ET.SubElement(eq, tag('field'), name='OP').text = 'EQ'
    a = ET.SubElement(eq, tag('value'), name='A')
    getter = ET.SubElement(a, tag('block'), type='variables_get', id='car_error_f')
    ET.SubElement(getter, tag('field'), name='VAR', id='vSensorF').text = 'sensorF'
    b = ET.SubElement(eq, tag('value'), name='B')
    num = ET.SubElement(b, tag('block'), type='math_number', id='car_error_ten')
    ET.SubElement(num, tag('field'), name='NUM').text = '10'
    ET.SubElement(decision, tag('statement'), name='DO0')
    for new, previous in ((1, 6), (2, 7), (3, 8)):
        for prefix in ('IF', 'DO'):
            child = old[prefix + str(previous)]
            child.set('name', prefix + str(new))
            if prefix == 'DO' and previous in (6, 7):
                # Original A3 if/else bodies are identical; keep one motor chain.
                body = deepcopy(child.find("b:block/b:statement[@name='DO0']/b:block", N))
                for field in body.findall('.//b:field', N):
                    if field.get('name') == 'VAR' and field.text == 'SPEED_STRAIGHT':
                        field.text = 'SPEED_CURVE'
                child.clear()
                child.set('name', prefix + str(new))
                child.append(body)
            decision.append(child)
    decision.append(old['ELSE'])
    if tail is not None:
        decision.append(tail)
    note(decision, 'Normal follow fallback: F=10 holds; left/right proportional steering. Lap finish, wide marker, short gap and sharp-turn states have priority. The preserved legacy F=0 loop counter is bypassed by the gap/turn states.')
    # Remove unused helpers and disabled boot tone; keep the existing stop helper.
    for block in list(root.findall('b:block', N)):
        if block.get('type') == 'procedures_defnoreturn':
            if block.find("b:field[@name='NAME']", N).text != 'stop':
                root.remove(block)
    for parent in list(root.iter()):
        for child in list(parent):
            if child.get('disabled') == 'true':
                parent.remove(child)
    variables = root.find('b:variables', N)
    for variable in list(variables):
        if variable.text in unused:
            variables.remove(variable)
    main.set('x', '40')
    main.set('y', '-1400')
    note(main, 'Start on the narrow line LEFT of the large finish patch, facing away from finish. Three-center-sensor control, sharp corners and short gaps. After departure/minimum run, sustained wide line latches finish stop. This is not measured lap localization. Button waits at boot only.')
    for block_id, text in (
        ('n0232', 'Read all five ADCs; preserve original raw telemetry.'),
        ('three1', 'Exclude A1/A5 from center F and weighted position. Their saved raw values now feed the separately confirmed outer sharp-turn assistance.'),
        ('n7010', 'Build F = 8*A4_on + 4*A3_on + 2*A2_on.'),
        ('sm0002', 'Curve base174/gain174/minimum15 after45 percent increase from120/120/10. Straight stages100/150/190/230 retain brief F6/F12 trim without advancing during correction. Strong side or unresolved trim resets stages.'),
        ('n0210', 'Original 115200-baud raw ADC/F telemetry; no new capture protocol.'),
    ):
        note(main.find(".//b:block[@id='%s']" % block_id, N), text)
    add_sharp_turns(root, main, decision)
    replace_normal_follow(main)
    streamline_loop_io(root, main)
    ids = {v.text: v.get('id') for v in root.find('b:variables', N)}
    for field in root.findall('.//b:field', N):
        if field.get('name') == 'VAR':
            field.set('id', ids[field.text])
    ET.indent(root, space='  ')
    (ROOT / 'car.xml').write_text(ET.tostring(root, encoding='unicode') + '\n', encoding='utf-8')
    print('Rewrote car.xml from the preserved legacy XML; export Arduino next.')


if __name__ == '__main__':
    rewrite()
