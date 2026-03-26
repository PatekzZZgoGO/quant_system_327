import importlib
import pkgutil
import inspect


class FactorRegistry:
    """
    👻 因子注册中心（插件系统）

    功能：
    - 自动扫描 factors 目录
    - 自动注册函数
    - 提供统一访问接口
    """

    def __init__(self):
        self._factors = {}

    def register(self, name, func, alias=None):
        self._factors[name] = func

        if alias:
            self._factors[alias] = func

    def get(self, name):
        return self._factors.get(name)

    def list_factors(self):
        return list(self._factors.keys())

    def load_from_package(self, package_name="features.factors"):
        """
        👻 自动扫描所有子模块
        """

        package = importlib.import_module(package_name)

        for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            module = importlib.import_module(module_name)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # 👻 只注册函数
                if inspect.isfunction(attr):
                    alias = getattr(attr, "alias", None)
                    self.register(attr_name, attr, alias)

        return self