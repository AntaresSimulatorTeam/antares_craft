from antares.api_conf.api_conf import APIconf
from antares.model.study import create_study_api
from antares.service.api_services.study_api import StudyApiService
from tests.antares.services.local_services.conftest import area_fr

api_host="https://antares-web-recette.rte-france.com"

token = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
         ".eyJzdWIiOiJ7XCJpZFwiOjE1NCxcInR5cGVcIjpcImJvdHNcIixcImltcGVyc29uYXRvclwiOjIsXCJncm91cHNcIjpbXX0iLCJpYXQiOjE3MzA3Mjg4NTgsIm5iZiI6MTczMDcyODg1OCwianRpIjoiM2M3MTJmNTItNTY1Yi00NzFlLTg5NWMtMTVkZDRjY2EyMmFiIiwiZXhwIjo4MDg5NzY4ODU4LCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlfQ.ytXsdGF-Aj7uj9bsnkOsQbU6OtyfU54I0Vl2pVFaOlo")
api = APIconf(api_host, token, False)
#study = create_study_api("ACrafttest-01", "860", api)
#area1=study.create_area("gozo")
#area1.create_thermal_cluster()
#study.create_area("toto")

api_service = StudyApiService(api, "9a5ef197-7f06-4c77-b085-3f360e12b23e")
api_service.read_areas()
