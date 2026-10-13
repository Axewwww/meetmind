# Manual Test Cases

| Test | Input | Expected behavior |
|---|---|---|
| TC01 | `Aisha will send the report by Friday.` | Likely task appears; owner Aisha; deadline Friday. |
| TC02 | `Prepare the demo slides.` | Likely task may appear; owner unassigned; deadline not specified; review flag yes. |
| TC03 | `The team discussed the budget.` | Should not be treated as a task unless wording includes a detected action commitment. |
| TC04 | Repeat the same action sentence twice. | Duplicate sentence should be removed in offline mode. |
| TC05 | Extract results and download CSV. | CSV file downloads and opens as a table. |
| TC06 | Use API mode with no key. | Application shows an error and asks the user to enter a key or switch to offline mode. |

Record actual observations and screenshots after running the application. Do not claim tests passed until you have executed them.
