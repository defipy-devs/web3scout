from ..abi.abi_load import ABILoad
from ..utils.connect import ConnectW3

class ViewContract():

    def __init__(self, connect: ConnectW3, abi: ABILoad, verbose = False):
        self.__connect = connect   
        self.__abi = abi 
        self.__w3 = self.__connect.get_w3()
        self.__contract = None
        self.__verbose = verbose

    def apply(self, address):
        contract_interface = self.get_contract_interface()
        contract = self.__w3.eth.contract(address=address, abi=contract_interface['abi'])
        view_fns = self.retrieve_view_funcs()

        view_fns_res = {}
        for k, fn_str in enumerate(view_fns) :
            try:
                fn_res = self._call_fn(contract, fn_str)
                fn_str_pout = self._str_output(f'[{k}]', fn_str+'()', max_len = 5)
                res = self._str_output(fn_str_pout, fn_res)
                view_fns_res[fn_str] = fn_res
                if(self.__verbose): print(res)
            except ValueError:
                print('function call error')

        return view_fns_res

    
    def retrieve_view_funcs(self):

        contract_interface = self.get_contract_interface()
        
        view_fns = []; c = 0
        for k, record in enumerate(contract_interface['abi']):
            if(record['type'] == 'function' and len(record['inputs']) == 0 and record['stateMutability'] == 'view'):
                c+=1
                if(self.__verbose): print(f"[{c}] View function: {record['name']}(), inputs: {record['inputs']}")
                view_fns.append(record['name'])   

        return view_fns    

    def get_contract_interface(self):
        fname = self.__abi.get_abi_path() 
        return self.__abi.get_abi_by_filename(fname)    


    def _concat_str(self, str0, max_len = None):
        max_len = 40 if max_len == None else max_len
        str0 = "".join([str0, " "])
        str_len = len(str0)
        return str0.ljust(max_len, ' ')
    
    def _str_output(self, in0, in1, max_len = None):    
        print_str_list = [self._concat_str(in0, max_len), str(in1)]    
        return ''.join(print_str_list)
    
    def _call_fn(self, contract, str_fn):
        attr = getattr(contract.functions, str_fn)
        return attr().call()
    