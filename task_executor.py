from lupa import LuaRuntime

class TaskExecutor:
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)

    def execute_lua_code(self, lua_code):
        try:
            lua_func = self.lua.execute(lua_code)
            result = lua_func()
            return result
        except Exception as e:
            return str(e)
