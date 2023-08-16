REGEX_REMOVE_ADS = r"(Dành cho).*?(miễn phí)"

REGEX_CUT_ANSWER = r'(Chứng minh|Lời giải|Hướng dẫn trả lời|Chứng minh|Giải thích|Trả lời|Bài giải|Kết quả|Giải chi tiết|Bài làm).*?[:]'

REGEX_COMMAND_REMOVE = r'(Nếu bạn có nhu cầu đặt lịch|Trên đây|Hãy|Mời|Nêu|Vui lòng|Xem thêm|Xin|Làm ơn|Lấy từ|Please|Cảm ơn|Tra cứu|Thanks|Tạm biệt|Goodbye).*?[.?!:»]'

VN_abbreviation = {"M.City", "V.I.P", "PGS.Ts", "MRS.", "Mrs.", "Man.United", "Mr.", "SHB.ĐN", "Gs.Bs", "U.S.A",
                   "TMN.CSG", "Kts.Ts", "R.Madrid", "Tp.", "T.Ư", "D.C", "Gs.Tskh", "PGS.KTS", "GS.BS", "KTS.TS",
                   "PGS-TS", "Co.", "S.H.E", "Ths.Bs", "T&T.HN", "MR.", "Ms.", "T.T.P", "TT.", "TP.", "ĐH.QGHN",
                   "Gs.Kts", "Man.Utd", "GD-ĐT", "T.W", "Corp.", "ĐT.LA", "Dr.", "T&T", "HN.ACB", "GS.KTS", "MS.",
                   "Prof.", "GS.TS", "PGs.Ts", "PGS.BS", "BT.", "Ltd.", "ThS.BS", "Gs.Ts", "SL.NA", "Th.S", "Gs.Vs",
                   "PGs.Bs", "T.O.P", "PGS.TS", "HN.T&T", "SG.XT", "O.T.C", "TS.BS", "Yahoo!", "Man.City", "MISS.",
                   "HA.GL", "GS.Ts", "TBT.", "GS.VS", "GS.TSKH", "Ts.Bs", "M.U", "Gs.TSKH", "U.S", "Miss.", "GD.ĐT",
                   "PGs.Kts", "St.", "Ng.", "Inc.", "Th.", "N.O.V.A"}

VN_exception = {"Wi-fi", "17+", "km/h", "M7", "M8", "21+", "G3", "M9", "G4", "km3", "m/s", "km2", "5g", "4G", "8K",
                "3g", "E9", "U21", "4K", "U23", "Z1", "Z2", "Z3", "Z4", "Z5", "Jong-un", "u19", "5s", "wi-fi", "18+",
                "Wi-Fi", "m2", "16+", "m3", "V-League", "Geun-hye", "5G", "4g", "Z3+", "3G", "km/s", "6+", "u21",
                "WI-FI", "u23", "U19", "6s", "4s"}

CLASS_PRIORITIZE = [
    'uitleg',
    'mw-parser-output',
    'loigiai',
    'answer',
    'accordion-detail',
    'answer-container',
    'anwsers-correct',
    'card-comment-content',
    'content_box',
    'box_content',
    'question-reason',
    'solution-item',
    'box-mes ipading',
    'main-container',
    'content-solution',
    'comment-author-kiemthecao'
]

USERAGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.0.0',
]

SITE_BLOCKED = [
    "xn--t-in-1ua7276b5ha.com",
    "từ-điển.com",
    "tratu.coviet.vn",
    "simonhoadalat.com",
    "hotcourses.vn",
    "tudienso.com",
    "dictionary.cambridge.org",
    "tenkhaisinh.com",
    "vi.wiktionary.org",
    "vtudien.com",
    "truyenhinhcapsongthu.net",
    "chunom.net"
]