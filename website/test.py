from intasend import APIService


API_PUBLISHABLE_KEY = 'ISPubKey_test_ca0331cb-8a01-4510-a711-e2260071ccb8'

API_TOKEN = 'ISSecretKey_test_c6f63b6f-06f6-441d-b5f0-dec432e2a0bd'

service= APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY,test=True)

create_order= service.collect.mpesa_stk_push(phone_number=25472000000, email='test@gmail.com',
                                             amount=100,narrative='Purchase of items')


print(create_order)