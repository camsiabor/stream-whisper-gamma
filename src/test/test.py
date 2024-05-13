import src.service.google.translator as googletrans

if __name__ == '__main__':
    print("hello")
    trans = googletrans.GoogleTranslator(url_suffix="hk")
    ret = trans.translate("hello", "zh", "en")
    print(ret)
