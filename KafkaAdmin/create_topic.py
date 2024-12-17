from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaConsumer
from contextlib import closing
import logging
# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bootstrap_servers = ['kafka-broker-1:9092', 'kafka-broker-2:9092', 'kafka-broker-3:9092']

topic_list = ['to-alert-system', 'to-notifier']

num_partitions = 1  
replication_factor = 3  

def list_topics_and_details():
    """ Stampa a video la lista dei topic e dei dettagli """
    consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
    topics = consumer.topics()  
    logger.info("\nDettagli dei topic disponibili:")

    for topic in sorted(topics):
        partitions = consumer.partitions_for_topic(topic)
        if partitions:
            logger.info(f"\nTopic: {topic}")
            logger.info(f"  Numero partizioni: {len(partitions)}")
            logger.info("  Dettagli sulle partizioni:")
            for partition in sorted(partitions):
                logger.info(f"    Partizione {partition}")
        else:
            logger.info(f"\nTopic: {topic}")
            logger.info("  Non ci sono partizioni disponibili per questo topic.")

    consumer.close()

def create_topic_if_not_exists(topic_list, num_partitions, replication_factor):
    with closing(KafkaAdminClient(bootstrap_servers=bootstrap_servers, client_id='kafka-admin-container')) as admin_client:
        with closing(KafkaConsumer(bootstrap_servers=bootstrap_servers)) as consumer:
            for topic in topic_list:
                if topic not in consumer.topics():
                    new_topic = NewTopic(
                        name=topic,
                        num_partitions=num_partitions,
                        replication_factor=replication_factor
                    )
                    try:
                        logger.info(f"\nCreazione del topic '{topic}'...")
                        admin_client.create_topics(new_topics=[new_topic], validate_only=False)
                        logger.info(f"Topic '{topic}' creato con successo, numero partizioni:{num_partitions} e fattore di replica:{replication_factor}.")
                    except Exception as e:
                        logger.error(f"Si è verificato un errore durante la creazione del topic, codice di errore: {e}")
                else:
                    logger.info(f"\nIl Topic '{topic}' esiste già.")