from fastapi import FastAPI, Depends, responses
from fastapi_pagination import Page, paginate
import crud
from schemas import HostsRead, DummyCreate, CpuDataThresholdOut, Params, CpuDataDetailedOut
from database import SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


@app.get("/get_hosts", response_model=list[HostsRead], name="Get a list of all the hosts in the hosts table.")
def get_hosts(db: Session = Depends(get_db)):
    return crud.get_host_list(db)


@app.get("/get_max_cpu", name="Get a list of all hosts and their maximum CPU utilization recorded.")
def get_hosts(db: Session = Depends(get_db)):
    return crud.get_max_cpu(db)


@app.get("/util_detailed_view/{host_ip}", response_model=Page[CpuDataDetailedOut],
         name="Get a detailed list of all data for a particular host ordered by time in descending order.")
async def get_util_detailed_view(host_ip: str, db: Session = Depends(get_db), params: Params = Depends()):
    return paginate(crud.get_detailed_host_view(db, host_ip), params)


@app.get("/crossed_threshold_periods", response_model=Page[CpuDataThresholdOut],
         name="Get a list of all periods when the CPU utilization was above 80%")
async def get_crossed_threshold_periods(db: Session = Depends(get_db), params: Params = Depends()):
    return paginate(crud.get_cpu_threshold_crossed_periods(db), params)


@app.put("/generate_dummy_entries", name="Generate dummy entries in the hosts and cpu_data tables.")
async def generate_dummy_entries(model: DummyCreate = Depends(), db: Session = Depends(get_db)):
    if model.entries_num < model.hosts_num:
        return responses.JSONResponse(content={'Failed': f"The number of entries({model.entries_num}) must be higher "
                                                         f"than the number of hosts({model.hosts_num})."},
                                      status_code=400)
    added_data = await crud.generate_dummy_entries(db, model.entries_num, model.hosts_num)
    customized_added_data = []
    for data in added_data:
        for host_id, entries_added in data.items():
            customized_added_data.append({f"Host ID: {host_id}": f"{entries_added} entries added."})
    return responses.JSONResponse(content={'Success': customized_added_data},
                                  status_code=200)


@app.delete("/clear_old_data", name="Delete any entries in the cpu_data table which are older than 7 days.")
async def clear_old_cpu_entries(db: Session = Depends(get_db)):
    deleted_rows = await crud.clear_old_cpu_entries(db)
    return responses.JSONResponse(
        content={'Success': f'{deleted_rows} rows older than 7 days {"were" if deleted_rows != 1 else "was"} deleted.'},
        status_code=200)
