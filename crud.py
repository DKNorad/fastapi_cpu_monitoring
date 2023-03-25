from random import randint
from sqlalchemy import func
from sqlalchemy.orm import Session
from time import time, strftime, localtime
from models import Host, CpuData
import schemas


def get_max_cpu(session: Session):
    """Return the maximum CPU utilization in percentage for all hosts in the form of dictionary"""
    host_ips = [r.ip for r in session.query(Host.ip)]
    max_cpu_hosts = {}
    for host_ip in host_ips:
        cpu_max = session.query(CpuData.host_id, func.max(CpuData.cpu_util))\
            .join(Host).filter(Host.ip == host_ip).all()[0]
        max_cpu_hosts[host_ip] = {"ID": cpu_max[0], "Max CPU": cpu_max[1]}
    session.close()
    return max_cpu_hosts


async def clear_old_cpu_entries(session: Session):
    """Delete any entries in the cpu_data table if the timestamp is older than 7 days from now"""
    count = session.query(CpuData).filter(CpuData.timestamp < (time() - 604800)).delete()
    session.commit()
    session.close()
    return count


def add_entries(session: Session, table, items: list = schemas.CpuDataBase | schemas.HostCreate):
    """Get a list with one or more items and add them as entries into the provided table"""
    newly_added_host_ids = []
    if table == "host":
        for host in items:
            host_obj = Host(ip=host)
            session.add(host_obj)
            session.flush()
            newly_added_host_ids.append(host_obj.id)
    elif table == "cpu_data":
        for host_id, cpu_util, timestamp in items:
            session.add(CpuData(host_id=host_id, cpu_util=cpu_util, timestamp=timestamp))
    session.commit()
    session.close()
    if table == "host":
        return newly_added_host_ids


def get_host_list(session: Session):
    """Get all the hosts from the 'hosts' table and return a list with the query objects"""
    hosts = session.query(Host).all()
    session.close()
    return hosts


def get_host_ids_list(session: Session):
    """Get all host ids from the 'hosts' table and return a list"""
    host_ids = [r.id for r in session.query(Host.id)]
    session.close()
    return host_ids


def get_cpu_data_by_host(session: Session, host_ip: str):
    """Get all data about a particular host from the 'cpu_data' table"""
    host_data = session.query(CpuData)\
        .filter(CpuData.host_id == session.query(Host).filter(Host.ip == host_ip))\
        .with_entities(CpuData.host_id, CpuData.cpu_util, CpuData.timestamp).all()
    session.close()
    return host_data


async def generate_dummy_entries(session: Session, entries_num: int, hosts_num: int):
    """
    Generate a nested list with random entries with random data and pass it to the add_entries function.
    Format: [[host_id1, cpu_util, timestamp], [host_id2, cpu_util, timestamp]]
    Returns: A list with dicts indicating the host ID created and the number of entries added for it.
    Format: [{host_id: num_of_entries}, {host_id: num_of_entries}, {host_id: num_of_entries}]
    """

    # Generate new IPs which are not already present in the table and pass them to the add_entries function.
    ips = []
    current_ips = [r.ip for r in session.query(Host.ip)]
    for i in range(0, hosts_num):
        successful = False
        while not successful:
            x3 = randint(1, 254)
            x4 = randint(1, 254)
            ip = ".".join(map(str, ([10, 3, x3, x4])))
            if ip not in current_ips:
                ips.append(ip)
                successful = True

    new_host_ids = add_entries(session, "host", ips)

    items = []
    r = entries_num % hosts_num
    n = hosts_num
    # Split requested number of entries equally
    entries_per_host = [entries_num // n] * (n - r) + [entries_num // n + 1] * r

    data_per_host_added = []
    for host_id in new_host_ids:
        num_of_entries = entries_per_host.pop()
        data_per_host_added.append({host_id: num_of_entries})
        for _ in range(num_of_entries):
            # get a random time between now and 14 days ago
            random_time = randint(int(time() - 1209600), int(time()))
            items.append([host_id, randint(0, 100), random_time])

    add_entries(session, "cpu_data", items)
    return data_per_host_added


def get_cpu_threshold_crossed_periods(session: Session):
    """Get a list of dicts with all the entries which have crossed the CPU util threshold of 80%."""
    q = session.query(CpuData) \
        .filter(CpuData.cpu_util > 80).with_entities(CpuData.host_id, CpuData.cpu_util, CpuData.timestamp) \
        .order_by(CpuData.host_id, CpuData.timestamp).all()

    crossed_periods = []
    for result in q:
        period = strftime('%Y-%m-%d %H:%M:%S', localtime(result.timestamp))
        crossed_periods.append({"host_id": result.host_id, "cpu_util": result.cpu_util, "time": period})
    return crossed_periods


def get_detailed_host_view(session: Session, host_ip):
    """Get a list of dicts with a detailed view of all the hosts."""
    detailed_view = []
    q = session.query(CpuData).join(Host).filter(Host.ip == host_ip).order_by(CpuData.timestamp.desc()).all()
    for result in q:
        period = strftime('%Y-%m-%d %H:%M:%S', localtime(result.timestamp))
        detailed_view.append({"host_id": result.host_id, "cpu_util": result.cpu_util, "time": period})
    return detailed_view
