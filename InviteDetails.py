from pydantic import BaseModel, BeforeValidator
from datetime import datetime
from typing import Annotated
import pytz

def validate_timezone(v: str) -> str:
    try:
        pytz.timezone(v)
        return v
    except pytz.UnknownTimeZoneError:
        raise ValueError(f'Invalid timezone: {v}')

TimezoneStr = Annotated[str, BeforeValidator(validate_timezone)]


class InviteInfo(BaseModel):
    TitleFont: str = "Classic"
    Title: str
    StartDate: datetime
    EndDate: datetime
    TimeZone: TimezoneStr
    Hosts : list
    Location: str
    MaxCapacity: int
    Cost: float
    GuestCanInviteFriends: bool
    Description: str
    RSVP_Options: str = "Emojis"
    GuestRequireApproval: bool = True








    
    