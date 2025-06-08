"""FastAPI 프로그램 - 5장"""

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date


import crud, schemas
from database import SessionLocal

# API 설명 정의
api_description = """  
이 API는 SportsWorldCentral(SWC) 판타지 풋볼 API의 정보를 읽기 전용으로 제공합니다.
제공되는 엔드포인트는 다음과 같습니다.

## 분석(analytics)
API의 상태 및 리그, 팀, 선수 수에 대한 정보를 제공합니다.

## 선수(players)
NFL 선수 목록을 조회하거나, 특정 player_id를 이용해 개별 선수 정보를 제공합니다.

## 점수(scoring)
NFL 선수의 경기 성적과 해당 성적을 기반으로 한 SWC 리그 판타지 점수를 제공합니다.

## 멤버십(membership)
SWC 판타지 풋볼 리그 전체와 각 리그에 속한 팀에 대한 정보를 제공합니다.
"""

#OpenAPI 명세에 추가 세부 정보가 추가된 FastAPI 생성자
app = FastAPI(
    description=api_description,  
    title="Sports World Central (SWC) Fantasy Football API",  
    version="0.1"  
)



# 데이터베이스 세션 의존성 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get(
    "/",
    summary="SWC 판타지 풋볼 API가 실행 중인지 확인합니다.",
    description="""이 엔드포인트를 사용하여 API가 정상적으로 작동하는지 확인할 수 있습니다. 
                  다른 API 호출을 하기 전에 먼저 이 엔드포인트를 통해 API의 상태를 확인하는 것이 좋습니다.""",
    response_description="메시지가 포함된 JSON 형식의 레코드입니다. API가 실행 중이면 성공 메시지를 반환합니다.",
    operation_id="v0_health_check",
    tags=["analytics"],
)
async def root():
    return {"message": "API 상태 확인 성공"}


@app.get(
    "/v0/players/",
    response_model=list[schemas.Player],
    summary="요청 매개변수에 일치하는 모든 SWC 선수를 가져옵니다.",
    description="""이 엔드포인트를 사용하여 SWC 선수 목록을 가져옵니다. 
                  매개변수를 사용하여 목록의 선수를 필터링할 수 있습니다. 
                  이름은 고유하지 않습니다. skip과 limit을 사용하여 API 페이지네이션을 수행합니다. 
                  선수 ID 값을 사용하여 개수를 세거나 로직을 수행하지 마세요. 
                  선수 ID는 순서가 보장되지 않는 내부 ID입니다.""",
    response_description="SWC 판타지 풋볼에 속한 NFL 선수 목록입니다. 팀에 속해 있지 않아도 됩니다.",
    operation_id="v0_get_players",
    tags=["players"],
)
def read_players(
    skip: int = Query(
        0, description="API 호출 시 목록의 시작 부분에서 건너뛸 항목의 수입니다."
    ),
    limit: int = Query(
        100, description="건너뛴 항목 이후에 반환할 최대 레코드 수입니다."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="레코드를 반환할 최소 변경 날짜입니다. 이 날짜 이전에 변경된 레코드는 제외됩니다.",
    ),
    first_name: str = Query(
        None, description="반환할 선수의 이름입니다."
    ),
    last_name: str = Query(None, description="반환할 선수의 성입니다."),
    db: Session = Depends(get_db),
):
    players = crud.get_players(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
        first_name=first_name,
        last_name=last_name,
    )
    return players


@app.get(
    "/v0/players/{player_id}",
    response_model=schemas.Player,
    summary="SWC 내부 선수 ID를 사용하여 선수 한 명을 가져옵니다.",
    description="""v0_get_players와 같은 다른 API 호출에서 얻은 SWC 선수 ID가 있다면, 
                  해당 선수 ID를 사용하여 이 API를 호출할 수 있습니다.""",
    response_description="한 명의 NFL 선수 정보입니다.",
    operation_id="v0_get_players_by_player_id",
    tags=["players"],
)
def read_player(player_id: int, db: Session = Depends(get_db)):
    player = crud.get_player(db, player_id=player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="선수를 찾을 수 없습니다.") # 번역 적용
    return player


@app.get(
    "/v0/performances/",
    response_model=list[schemas.Performance],
    summary="요청 매개변수에 일치하는 모든 주간 성적을 가져옵니다.",
    description="""이 엔드포인트를 사용하여 SWC 선수들의 주간 성적 목록을 가져옵니다. 
                  skip과 limit을 사용하여 API 페이지네이션을 수행합니다. 
                  성적 ID는 내부 ID이며 순서가 보장되지 않으므로, 
                  개수를 세거나 로직에 사용하지 마세요.""",
    response_description="여러 선수들의 주간 성적 목록입니다.",
    operation_id="v0_get_performances",
    tags=["scoring"],
)
def read_performances(
    skip: int = Query(
        0, description="API 호출 시 목록의 시작 부분에서 건너뛸 항목의 수입니다."
    ),
    limit: int = Query(
        100, description="건너뛴 항목 이후에 반환할 최대 레코드 수입니다."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="레코드를 반환할 최소 변경 날짜입니다. 이 날짜 이전에 변경된 레코드는 제외됩니다.",
    ),
    db: Session = Depends(get_db),
):
    performances = crud.get_performances(
        db, skip=skip, limit=limit, min_last_changed_date=minimum_last_changed_date
    )
    return performances


@app.get(
    "/v0/leagues/{league_id}",
    response_model=schemas.League,
    summary="리그 ID로 리그 한 개를 가져옵니다.",
    description="""이 엔드포인트를 사용하여 사용자가 제공한 리그 ID에 일치하는 단일 리그를 가져옵니다.""",
    response_description="SWC 리그 정보입니다.",
    operation_id="v0_get_league_by_league_id",
    tags=["membership"],
)
def read_league(league_id: int, db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id=league_id)
    if league is None:
        raise HTTPException(status_code=404, detail="리그를 찾을 수 없습니다.") # 번역 적용
    return league


@app.get(
    "/v0/leagues/",
    response_model=list[schemas.League],
    summary="요청 매개변수에 일치하는 모든 SWC 판타지 풋볼 리그를 가져옵니다.",
    description="""이 엔드포인트를 사용하여 SWC 판타지 풋볼 리그 목록을 가져옵니다. 
                  skip과 limit을 사용하여 API 페이지네이션을 수행합니다. 
                  리그 이름은 고유하지 않을 수 있습니다. 
                  리그 ID는 순서가 보장되지 않는 내부 ID이므로, 
                  개수를 세거나 로직에 사용하지 마세요.""",
    response_description="SWC 판타지 풋볼 웹사이트의 리그 목록입니다.",
    operation_id="v0_get_leagues",
    tags=["membership"],
)
def read_leagues(
    skip: int = Query(
        0, description="API 호출 시 목록의 시작 부분에서 건너뛸 항목의 수입니다."
    ),
    limit: int = Query(
        100, description="건너뛴 항목 이후에 반환할 최대 레코드 수입니다."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="레코드를 반환할 최소 변경 날짜입니다. 이 날짜 이전에 변경된 레코드는 제외됩니다.",
    ),
    league_name: str = Query(
        None, description="반환할 리그의 이름입니다. SWC 내에서 고유하지 않을 수 있습니다."
    ),
    db: Session = Depends(get_db),
):
    leagues = crud.get_leagues(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
        league_name=league_name,
    )
    return leagues


@app.get(
    "/v0/teams/",
    response_model=list[schemas.Team],
    summary="요청 매개변수에 일치하는 모든 SWC 판타지 풋볼 팀을 가져옵니다.",
    description="""이 엔드포인트를 사용하여 SWC 판타지 풋볼 팀 목록을 가져옵니다. 
                  skip과 limit을 사용하여 API 페이지네이션을 수행합니다. 
                  팀 이름은 고유하지 않을 수 있습니다. 
                  v0_get_players와 같은 다른 쿼리에서 팀 ID를 얻었다면, 
                  이 쿼리의 팀 ID와 일치시킬 수 있습니다. 
                  팀 ID는 순서가 보장되지 않는 내부 ID이므로, 
                  개수를 세거나 로직에 사용하지 마세요.""",
    response_description="SWC 판타지 풋볼 웹사이트의 팀 목록입니다.",
    operation_id="v0_get_teams",
    tags=["membership"],
)
def read_teams(
    skip: int = Query(
        0, description="API 호출 시 목록의 시작 부분에서 건너뛸 항목의 수입니다."
    ),
    limit: int = Query(
        100, description="건너뛴 항목 이후에 반환할 최대 레코드 수입니다."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="레코드를 반환할 최소 변경 날짜입니다. 이 날짜 이전에 변경된 레코드는 제외됩니다.",
    ),
    team_name: str = Query(
        None,
        description="반환할 팀의 이름입니다. SWC 전체에서는 고유하지 않지만, 리그 내에서는 고유합니다.",
    ),
    league_id: int = Query(
        None, description="반환할 팀의 리그 ID입니다. SWC 내에서 고유합니다."
    ),
    db: Session = Depends(get_db),
):
    teams = crud.get_teams(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
        team_name=team_name,
        league_id=league_id,
    )
    return teams


@app.get(
    "/v0/counts/",
    response_model=schemas.Counts,
    summary="SWC 판타지 풋볼의 리그, 팀, 선수 수를 가져옵니다.",
    description="""이 엔드포인트를 사용하여 SWC 판타지 풋볼의 리그, 팀, 선수 수를 계산합니다. 
                  v0_get_leagues, v0_get_teams 또는 v0_get_players에서 skip과 limit과 함께 사용하세요. 
                  다른 API를 호출하는 대신 이 엔드포인트를 사용하여 개수를 가져오세요.""",
    response_description="SWC 판타지 풋볼 웹사이트의 팀 목록입니다.", # 이 부분은 Counts 스키마에 대한 응답 설명이므로, "팀 목록"이 아닌 "개수 정보"와 같은 설명이 더 적절할 수 있습니다. 원문 유지.
    operation_id="v0_get_counts",
    tags=["analytics"],
)
def get_count(db: Session = Depends(get_db)):
    counts = schemas.Counts(
        league_count=crud.get_league_count(db),
        team_count=crud.get_team_count(db),
        player_count=crud.get_player_count(db),
    )
    return counts
