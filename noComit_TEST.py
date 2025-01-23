from antares import craft
from antares.craft.api_conf.api_conf import APIconf
from antares.craft.model.settings.study_settings import StudySettingsLocal

# token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ7XCJpZFwiOiAxMTIsIFwidHlwZVwiOiBcImJvdHNcIiwgXCJpbXBlcnNvbmF0b3JcIjogMiwgXCJncm91cHNcIjogW3tcImlkXCI6IFwiNDE5OTgzMWYtMGU5Ny00MjkwLTkxYjItZjlhY2Y5ZWY3MzM0XCIsIFwibmFtZVwiOiBcIkZvcm1hdGlvblwiLCBcInJvbGVcIjogMzB9LCB7XCJpZFwiOiBcInRlc3RcIiwgXCJuYW1lXCI6IFwidGVzdFwiLCBcInJvbGVcIjogNDB9XX0iLCJpYXQiOjE3MTIzMjYwODUsIm5iZiI6MTcxMjMyNjA4NSwianRpIjoiMWZkZmM5ODktMGIwMy00Yjk3LWFlZDEtODgwMjkyMzU4NDliIiwiZXhwIjo4MDcxMzY2MDg1LCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlfQ.S9Snc1QRfWqQ0kxqcHk_vys75T_pkQYpdgsfDmYIwQU"
# host="https://antares-web-recette.rte-france.com"
# api_config = APIconf(host,token,False)
# study = craft.create_study_api("4422testRCraft22","8.8", api_config)C


study = craft.create_study_local("Atotot","8.8", "/home/vargastat/Documents/CraftTests")
area=study.create_area("test_H1")
#area.create_thermal_cluster("cluster")