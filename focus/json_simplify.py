from bs4 import BeautifulSoup

def simplify_referrals(records):
    d = {'referrals': {}}
    for id in records:
        ref = {}
        for k in records[id]:
            if not k.startswith('CUSTOM_'):
                continue
            violation = records[id][k]
            if violation is not None:
                if type(violation) is list:
                    violation = next(filter(bool, list(violation)), None)
                if violation.lower().strip() == "other" or len(violation) < 2:
                    continue

                if k.endswith('_1'):
                    ref['violation'] = violation
                else:
                    ref['other_violation'] = violation
        ref['creation_date'] = records[id]['CREATION_DATE']
        ref['display'] = records[id]['DISPLAY'] == 'Y'
        ref['entry_date'] = records[id]['ENTRY_DATE']
        ref['last_updated'] = records[id]['LAST_UPDATED']
        ref['notification_sent'] = records[id]['NOTIFICATION_SENT']
        ref['processed'] = records[id]['PROCESSED'] == 'Y'
        ref['id'] = id
        if records[id]['SUSPENSION_BEGIN']:
            ref['suspension_begin'] = records[id]['SUSPENSION_BEGIN']
            ref['suspension_end'] = records[id]['SUSPENSION_END']
        ref['school_year'] = records[id]['SYEAR']
        ref['school'] = records[id]['_school']

        student_name = BeautifulSoup(records[id]['_student'], 'html.parser').text.strip().split(', ')
        staff_name = records[id]['_staff_name'].split(',')

        ref['teacher'] = staff_name[1] + ' ' + staff_name[0]
        ref['name'] = student_name[1] + ' ' + student_name[0]
        ref['grade'] = int(records[id]['_grade'])

        d['referrals'][ref['id']] = ref

    return d

def simplify_final_grades(records, type):
    d = {type: {}}
    for field in records['result']['grades'].values():
        s = {}
        s['id'] = field['id']
        s['syear'] = int(field['syear'])
        s['name'] = field['course_title']
        s['affects_gpa'] = bool(field['affects_gpa'])
        if s['affects_gpa']:
            s['gpa_points'] = float(field['gpa_points'])
            s['weighted_gpa_points'] = float(field['weighted_gpa_points'])
        s['teacher'] = field['teacher'].split(', ')[1] + ' ' + field['teacher'].split(', ')[0]
        s['teacher'] = s['teacher'].replace(' (Teacher)', '')
        s['course_id'] = field['course_period_id']
        s['course_num'] = field['course_num']
        s['percent_grade'] = int(field['percent_grade'])
        s['letter_grade'] = field['grade_title']
        if field['credits'] and field['credits_earned']:
            s['credits'] = float(field['credits'])
            s['credits_earned'] = float(field['credits_earned'])
        s['grade_level'] = int(field['gradelevel_title'])
        s['last_updated'] = field['last_updated_date']
        s['location'] = field['location_title']
        s['mp_id'] = field['marking_period_id'].replace('E', '')
        s['mp_name'] = field['_mp_title']
        if field['comment']:
            s['comment'] = field['comment']

        if field['grad_subject_id']:
            s['subject'] = records['result']['defaults']['grad_subject']['1'][field['grad_subject_id']]['title']

        if field['last_updated_user'] in records['result']['defaults']['teacher']['1']:
            last_updated_by = records['result']['defaults']['teacher']['1'][field['last_updated_user']]['title'].split(', ')
            s['last_updated_by'] = last_updated_by[1] + ' ' + last_updated_by[0]
            s['last_updated_by'] = s['last_updated_by'].replace(' (Teacher)', '')

        grade_scales = records['result']['defaults']['grade_scale']
        grade_scales.update(records['result']['domains']['grade_scale'])
        grade_scale_id = field['grade_scale_id']
        for k in grade_scales:
            for id in grade_scales[k]:
                if id == grade_scale_id:
                    s['scale'] = grade_scales[k][id]['title']

        d[type][s['id']] = s

    return d
