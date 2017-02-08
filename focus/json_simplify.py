def simplify_final_grades(records, type):
    d = {type: []}
    for field in records['result']['grades'].values():
        s = {}
        s['id'] = int(field['id'])
        s['syear'] = int(field['syear'])
        s['name'] = field['course_title']
        s['affects_gpa'] = bool(field['affects_gpa'])
        if s['affects_gpa']:
            s['gpa_points'] = float(field['gpa_points'])
            s['weighted_gpa_points'] = float(field['weighted_gpa_points'])
        s['teacher'] = field['teacher'].split(', ')[1] + ' ' + field['teacher'].split(', ')[0]
        s['course_id'] = int(field['course_period_id'])
        s['course_num'] = field['course_num']
        s['percent_grade'] = int(field['percent_grade'])
        s['letter_grade'] = field['grade_title']
        if field['grad_subject_short_name']:
            s['subject'] = field['grad_subject_short_name']
        if field['credits'] and field['credits_earned']:
            s['credits'] = float(field['credits'])
            s['credits_earned'] = float(field['credits_earned'])
        s['grade_level'] = int(field['gradelevel_title'])
        s['last_updated'] = field['last_updated_date']
        s['location'] = field['location_title']
        s['semester'] = int(field['_mp_title'].split(' ')[1])
        if field['comment']:
            s['comment'] = field['comment']

        if field['last_updated_user'] in records['result']['defaults']['teacher']['1']:
            last_updated_by = records['result']['defaults']['teacher']['1'][field['last_updated_user']]['title'].split(', ')
            s['last_updated_by'] = last_updated_by[1] + ' ' + last_updated_by[0]

        grade_scales = records['result']['defaults']['grade_scale']
        grade_scales.update(records['result']['domains']['grade_scale'])
        grade_scale_id = field['grade_scale_id']
        for k in grade_scales:
            for id in grade_scales[k]:
                if id == grade_scale_id:
                    s['scale'] = grade_scales[k][id]['title']

        d[type].append(s)

    return d