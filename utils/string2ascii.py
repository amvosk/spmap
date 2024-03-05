
symbols = (
    u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
    u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA"
)
tr = {ord(a): ord(b) for a, b in zip(*symbols)}

def ru2ascii(text):
    return text.translate(tr)

if __name__ == '__main__':
    parient_names = ['Виктор', 'Viktor', 'Викtor', 'Viktor123', 'Виктор2345', 'Викtorр2345', '123Викtorр']
    for parient_name in parient_names:
        print(parient_name, string2ascii(parient_name))