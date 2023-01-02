"""
app.py

Implements App
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"


class App:
    """
    Use this class to propagate/persist variables throughout package
    """

    __conf = {
        "today": "",
        "ending_date": "",
        "ndays": "",
        "lags": "",
        "local": "",
        "dev": "",
        "aws_account_id": "",
    }
    __setters = [key for key in __conf.keys()]

    def config(name):
        """
        Getter
        """
        return App.__conf[name]

    def set(name: str, value: str):
        """
        Setter. Update __conf item for given key

        ::param name: variable name
        ::param value: variable value
        """
        if name in App.__setters:
            App.__conf[name] = value

        # raise NameError if key is not set defined in __conf
        else:
            raise NameError("Key not initialized")
