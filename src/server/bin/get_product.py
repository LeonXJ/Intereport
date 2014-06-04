#!/usr/bin/python2.7

if __name__ == '__main__':
    import sys
  
    from ir_config import IRConfig
    from ir_text import IRText
    from ir_mongodb_helper import IRCollection

    config = IRConfig.get_instance()
    config.load(sys.argv[1])
    product_name = config.get('bug_product_name')
    
    products = dict()

    basic = IRCollection('bug_db_name', 'bug_basic_collection_name', 'r')
    cursor = basic.find(None)
    for bug in cursor:
        product = bug[product_name]
        if product not in products:
            products[product] = 0
        products[product] += 1

    product_list = products.items()
    product_list.sort(cmp=lambda x,y:cmp(x[1],y[1]), reverse=True)

    prefix = '' if sys.argv.__len__() < 3 else sys.argv[2]
    surfix = '' if sys.argv.__len__() < 4 else sys.argv[3]
    threshold = 100 if sys.argv.__len__() <5 else int(sys.argv[4])
    for product in product_list:
        if product[1] < threshold:
            break
        print '%s%s%s <!--%d-->' % (prefix, product[0], surfix, product[1])
    

