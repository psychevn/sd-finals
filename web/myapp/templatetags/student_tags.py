from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_exam_result(exam_results, exam_id):
    try:
        return exam_results.filter(exam_id=exam_id).first()
    except:
        return None 