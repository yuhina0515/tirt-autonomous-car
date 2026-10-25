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
                             both, either, sub, add, anyof)
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
        'SPEED_CURVE': ('int', 100),
        'TURN_OUTER_PWM': ('int', 100),
        'TURN_INNER_PWM': ('int', 95),
        'TURN_TIMEOUT_MS': ('unsigned long', 800),
        'TURN_MIN_MS': ('unsigned long', 30),
        'TURN_MEMORY_MS': ('unsigned long', 250),
        'TURN_CENTER_CLEAR_MS': ('unsigned long', 80),
        'TURN_DIRECTION_CONFIRM_MS': ('unsigned long', 15),
        'TURN_CONFIRM_COUNT': ('int', 3),
        'turnDirection': ('int', 0),
        'turnActive': ('int', 0),
        'turnFault': ('int', 0),
        'turnConfirm': ('int', 0),
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
        'GAP_PWM': ('int', 70),
        'GAP_TIMEOUT_MS': ('unsigned long', 250),
        'gapActive': ('int', 0),
        'gapAt': ('unsigned long', 0),
        'gapElapsed': ('unsigned long', 0),
        'gapConfirm': ('int', 0),
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
             cond(ge('turnElapsed', 'TURN_TIMEOUT_MS'),
                  [setv('turnFault', 1), setv('turnActive', 0), call('stop')], [
                 cond(both(ge('turnElapsed', 'TURN_MIN_MS'), anyof('sensorF', [4, 6, 12])),
                      [setv('turnConfirm', add('turnConfirm', 1))],
                      [setv('turnConfirm', 0)]),
                 cond(ge('turnConfirm', 'TURN_CONFIRM_COUNT'), done, [
                     cond(ge('turnConfirm', 1), capture_drive,
                          [cond(eq('turnDirection', -1), left, right)])])])]
    function = exporter.block('procedures_defnoreturn')
    function.set('x', '900')
    function.set('y', '0')
    exporter.field(function, 'NAME', 'sharp_turn')
    exporter.field(function, 'TYPE', 'void')
    exporter.statement(function, 'STACK', pivot)
    note(function, 'Bounded sharp-corner pivot. After minimum30ms, F4/F6/F12 starts forward differential capture instead of continued reverse. Three consecutive captures finish the turn at curve PWM100, not straight150. Timeout latches stop; no measured angle or automatic restart.')
    root.append(function)

    # A short gap has its own fixed deadline and never inherits a pivot command.
    gap_drive = [('digitalwrite', '7', 0), ('pwm', '5', 'GAP_PWM'),
                 ('digitalwrite', '4', 1), ('pwm', '6', 'GAP_PWM')]
    def gap_wheels(left_pwm, right_pwm):
        return [('digitalwrite', '7', 0), ('pwm', '5', left_pwm),
                ('digitalwrite', '4', 1), ('pwm', '6', right_pwm)]
    gap_capture = [cases([
        (eq('sensorF', 8), gap_wheels(25, 'GAP_PWM')),
        (eq('sensorF', 12), gap_wheels(45, 'GAP_PWM')),
        (eq('sensorF', 2), gap_wheels('GAP_PWM', 25)),
        (eq('sensorF', 6), gap_wheels('GAP_PWM', 45))], gap_drive)]
    gap = [setv('gapElapsed', sub('turnNow', 'gapAt')),
           cond(ge('gapElapsed', 'GAP_TIMEOUT_MS'),
                [setv('turnFault', 1), setv('gapActive', 0), call('stop')], [
               cond(anyof('sensorF', [2, 4, 6, 8, 12]),
                    [setv('gapConfirm', add('gapConfirm', 1))], [setv('gapConfirm', 0)]),
               cond(either(ge('gapConfirm', 3), eq('sensorF', 14)),
                    [setv('gapActive', 0), setv('turnDirection', 0),
                     setv('whiteCount', 0)] + gap_capture, gap_capture)])]
    function = exporter.block('procedures_defnoreturn')
    function.set('x', '900')
    function.set('y', '650')
    exporter.field(function, 'NAME', 'cross_gap')
    exporter.field(function, 'TYPE', 'void')
    exporter.statement(function, 'STACK', gap)
    note(function, 'Short gap PWM70 with fixed250ms deadline. On side-line return, forward differential capture starts immediately (25/70 or45/70 mirrored). No reverse in gap state. Three narrow samples finish; wide line returns to marker handling.')
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
    before = [setv('turnNow', ('millis',)),
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
                  cond(eq('sensorF', 0), [cond(
                            both(either(eq('turnDirection', -1), eq('turnDirection', 1)),
                                 le('turnAge', 'TURN_MEMORY_MS')), [
                      setv('turnActive', 1), setv('turnAt', 'turnNow'),
                      setv('turnConfirm', 0)], [
                      setv('gapActive', 1), setv('gapAt', 'turnNow'),
                      setv('gapConfirm', 0)])])])]
    head = exporter.chain(before)
    last = head
    while last.find('b:next/b:block', N) is not None:
        last = last.find('b:next/b:block', N)
    wrapper = exporter.stmt(cases([
        (either(eq('turnFault', 1), eq('lapDone', 1)), [call('stop')]),
        (both(eq('LIFT_ENABLED', 1), either(eq('liftState', 1), eq('liftState', 2))),
         [call('lift_control')]),
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
        if name in ('SPEED_STRAIGHT', 'TURN_KP'):
            block.find(".//b:field[@name='NUM']", N).text = str(
                150 if name == 'SPEED_STRAIGHT' else 100)
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
        ('three1', 'Exclude A1 and A5 from decisions; control uses A4/A3/A2 only.'),
        ('n7010', 'Build F = 8*A4_on + 4*A3_on + 2*A2_on.'),
        ('sm0002', 'Position weights: A4=-1, A3=0, A2=+1. Integer proportional inner PWM; minimum5.'),
        ('n0210', 'Original 115200-baud raw ADC/F telemetry; no new capture protocol.'),
    ):
        note(main.find(".//b:block[@id='%s']" % block_id, N), text)
    add_sharp_turns(root, main, decision)
    ET.indent(root, space='  ')
    (ROOT / 'car.xml').write_text(ET.tostring(root, encoding='unicode') + '\n', encoding='utf-8')
    print('Rewrote car.xml from the preserved legacy XML; export Arduino next.')


if __name__ == '__main__':
    rewrite()
