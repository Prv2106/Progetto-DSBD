from confluent_kafka.admin import AdminClient
from confluent_kafka import KafkaException
import time 
import create_topic as ct
import logging
# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from confluent_kafka.admin import AdminClient, KafkaException
import logging
import create_topic as ct

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_metadata():
    """Recupera e stampa i metadati del cluster Kafka."""
    admin_client = AdminClient({'bootstrap.servers': ','.join(ct.bootstrap_servers)})
    try:
        logger.info("Recupero dei metadati dal cluster Kafka...")
        metadata = admin_client.list_topics(timeout=10)

        if not metadata.brokers:
            logger.warning("Nessun broker trovato nel cluster.")
            return
        
        logger.info("Broker nel cluster Kafka:")
        for broker in metadata.brokers.values():
            logger.info(f"Broker ID: {broker.id}, Host: {broker.host}, Porta: {broker.port}")

        if not metadata.topics:
            logger.warning("Nessun topic trovato nel cluster.")
            return

        logger.info("Topic e partizioni nel cluster Kafka:")
        for topic, topic_metadata in metadata.topics.items():
            logger.info(f"Topic: {topic}")
            if topic_metadata.error:
                logger.error(f"Errore per il topic '{topic}': {topic_metadata.error}")
            else:
                for partition_id, partition_metadata in topic_metadata.partitions.items():
                    leader = partition_metadata.leader
                    replicas = partition_metadata.replicas
                    isrs = partition_metadata.isrs
                    logger.info(f"  Partizione {partition_id}:")
                    logger.info(f"    Leader: Broker {leader}")
                    logger.info(f"    Repliche: {replicas}")
                    logger.info(f"    Repliche In-Sync (ISR): {isrs}")

    except KafkaException as e:
        logger.error(f"Errore durante il recupero dei metadati: {e}")
    except Exception as e:
        logger.exception(f"Errore imprevisto durante il recupero dei metadati: {e}")
    finally:
        logger.info("Operazione di recupero metadati completata.")
        
        

if __name__ == "__main__":
    
    logger.info("Preparazione dell'admin... (L'operazione richide circa 30 secondi)")
    time.sleep(30)
    
    try:
        logger.info("Creazione dei topic (se non esistenti...)\n")
        ct.create_topic_if_not_exists(ct.topic_list, num_partitions=ct.num_partitions, replication_factor=ct.replication_factor)
        logger.info("Stampa dei dettagli dei topic...")
        ct.list_topics_and_details()        
    except Exception as e:
        logger.error(f"Errore, codice di errore: {e}")
        exit(1)

    while True:
        time.sleep(10)
        get_metadata()
