from builder_expanded_eval import judge
from rag_poc.models import Plan,Query

def test_wait_is_reported_as_missed_opportunity_not_wrong_query():
    assert judge(Plan('wait',None),{'action':'retrieve','query_fields':{'name':'Chai'}})=='missed_retrieve'
    assert judge(Plan('wait',None),{'action':'wait'})=='appropriate_wait'

def test_wrong_entity_and_unjustified_query_are_distinct():
    assert judge(Plan('retrieve',Query(name='Chang')),{'action':'retrieve','query_fields':{'name':'Chai'}})=='wrong_query'
    assert judge(Plan('retrieve',Query(name='Chai')),{'action':'wait'})=='unjustified_retrieve'

def test_sql_equivalent_case_and_numbers_not_false_failure():
    assert judge(Plan('retrieve',Query(name='CHAI',min_price=10.0)),{'action':'retrieve','query_fields':{'name':'Chai','min_price':10}})=='correct_retrieve'


def test_unrequested_order_change_is_review_not_proven_correct():
    assert judge(Plan('retrieve',Query(name='Chai',order='price_desc')),{'action':'retrieve','query_fields':{'name':'Chai'}})=='query_variant_review'
