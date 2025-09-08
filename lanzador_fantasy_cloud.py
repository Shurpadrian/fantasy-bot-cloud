import generador_clasificacion_cloud
import generador_fixtures_cloud
import generador_jugadores_cloud
import generador_base_cloud
import generador_kpis_cloud
import enviar_telegram_cloud

def run_all():
    generador_clasificacion_cloud.run()
    generador_fixtures_cloud.run()
    generador_jugadores_cloud.run()
    generador_base_cloud.run()
    generador_kpis_cloud.run()
    enviar_telegram_cloud.run()

if __name__ == "__main__":
    run_all()
