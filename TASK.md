● Updated Plan for Attendance Closure Feature

  Corrected Understanding:
  - We're not closing commissions themselves
  - We're allowing parliamentarians to mark their attendance submission as closed for a specific commission within a settlement run
  - This signals to presidents that the parliamentarian has finished submitting all their attendances for that commission in the current settlement run

  Implementation Steps:

  Phase 1: Data Structure
  - Analyze current attendance model structure
  - Add "Abschluss" field to attendance records (marks attendance submission as closed for that commission/settlement run)

  Phase 2: UI Updates
  - Add "Abschluss" checkbox to attendance add form
  - In settlement runs overview: show status per parliamentarian indicating if they've marked their attendance as closed for each commission

  Phase 3: Control Logic
  - Visual indicators showing which parliamentarians have closed their attendance for each commission
  - Gray out checkboxes for parliamentarians who haven't marked as closed
  - Control list showing which parliamentarians haven't closed their attendance for commissions in the current settlement run
