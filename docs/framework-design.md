# Framework design

This page explains the decisions behind the framework and the alternatives that were not chosen.

## 1. One app, tested through its API and its UI

The Notes app has a web UI and a REST API on one backend. The test pyramid applies:

- Most rules are checked at the API level, which is fast and stable: validation, status codes,
  authorisation and the contract. There are 32 such tests.
- The browser tests only check what a user sees and does. There are 9 of them.
- A few hybrid tests check that the two sides agree. There are 5 of them.

## 2. Set-up through the API, never through the UI

UI tests need a logged-in user with some notes. Typing that into forms in every test would be slow,
and it would repeat the login test hundreds of times. So instead:

- the `account` fixture registers a user with one API call;
- the `notes_page` fixture puts that user's API token into `localStorage` before the page loads,
  which is the same place the app itself keeps it after a login. The browser starts out logged in;
- notes for a test are created with `create_note` API calls.

The login form is still tested, once, in `tests/ui/test_login.py`.

## 3. Every test has its own user

Each test registers a new user with a unique e-mail (`uuid`) and deletes the user afterwards, in the
fixture's teardown, which also runs after a failure. The results:

- No test depends on another test, or on the order in which tests run.
- Tests run in parallel safely with `pytest-xdist -n 4`, and each browser job in CI runs in parallel
  with the others.
- The public demo site is left clean.

A test that changes the password updates the mutable `Account` object, so the teardown can still log
in. If the clean-up cannot log in, it gives a warning rather than an error: a test result should not
depend on whether the clean-up worked.

## 4. The API client returns responses; it does not assert

`NotesApiClient` methods return `requests.Response`. Tests decide what is right. This way the same
client serves happy-path tests (200/201) and negative tests (400, 401, 404, 409). If a client method
asserted "200", the negative tests would need a second client.

The client keeps a `requests.Session`, which reuses connections, and the login token, which it sends
as `x-auth-token`.

## 5. Contracts with pydantic

`models.py` describes each response body. `ApiResponse[Note].model_validate(json)` checks:

- every field is present and has the right type;
- `category` is one of `Home`, `Work`, `Personal` (a `Literal`);
- there are no unknown fields (`extra="forbid"`). A field that the backend adds or renames shows up
  as a failing test straight away, not as a silent change.

The generic `ApiResponse[T]` models the envelope (`success`, `status`, `message`, `data`) once, for
every endpoint.

## 6. Page Objects without assertions; `expect` in tests

Page Objects (`LoginPage`, `NotesPage`) hold locators and actions. Locators use the app's
`data-testid` attributes (`get_by_test_id`), which do not change when the text or the layout does.

Assertions are in the tests, with Playwright's `expect(locator).to_have_text(...)`. This waits until
the condition is true or the timeout ends, so there are no `sleep` calls and no flaky timing checks.

`NotesPage.wait_until_loaded()` waits for whichever appears first: the progress text (when notes
exist) or the "no notes" message (when there are none). It uses `locator.or_()` and
`filter(visible=True)`, because the progress element is in the DOM but hidden on an empty list.

## 7. Configuration from environment variables

`framework/config.py` reads `NOTES_APP_URL`, `NOTES_API_URL` and two timeouts, with defaults for the
public demo. The same code then runs against a local copy, a staging copy or the demo, and CI needs no
config files. `Settings` is a frozen dataclass and is created once per run (a session fixture).

## 8. Markers and selection

`api`, `ui`, `e2e`, `smoke` and `demo` are declared in `pytest.ini`, and `--strict-markers` fails a
run that uses a misspelt marker. CI uses the markers to split the jobs: `-m api` runs without a
browser, and `-m "ui or e2e"` runs once per browser. The demo tests carry `demo`, which `addopts`
leaves out (`-m "not demo"`), so they only run when asked for.

## 9. Reports and failure evidence

- **pytest-html** writes one self-contained file, which is easy to keep as a CI artifact or to send to
  someone. A `pytest_runtest_makereport` hook adds a full-page screenshot to every failed UI test.
  `pytest_configure` adds the app and API URLs to the environment table.
- **Playwright** keeps a screenshot, a video and a trace of every failed UI test
  (`--screenshot=only-on-failure --video=retain-on-failure --tracing=retain-on-failure`). Passing
  tests keep nothing, so the artifacts stay small. The trace is usually the quickest way to see
  why a test failed.
- **The GitHub run summary** shows a pass/fail table per job, built from the JUnit XML by
  `.github/scripts/summary.py`, so nobody has to download an artifact to see what failed.

## 10. Failing on purpose: the report demo

`tests/demo` has one test for each kind of non-passing result, so the report can be shown without
breaking real tests:

- **failed**: a UI assertion with a screenshot, and an API assertion that includes the API's message;
- **skipped**: `pytest.skip` with a reason;
- **xfailed**: `xfail(strict=True)`. A known bug is recorded without failing the run. Once the bug is
  fixed, the test passes, and `strict` turns that into a failure, as a reminder to remove the mark.

## 11. Public demo site: blocking ads

The demo site loads ads and trackers. They slow down page loads, and an ad can cover a button. The
`app_page` fixture blocks those hosts with `context.route(...)`, before the first page is opened.

## 12. CI

- **lint** runs first, and the test jobs need it to pass. A formatting slip costs a few seconds,
  not a full browser run.
- **The browser matrix** uses `fail-fast: false`, so a Firefox-only problem does not hide the
  Chromium and WebKit results.
- **Each browser job** installs only its own browser (`playwright install --with-deps <browser>`).
- **A nightly cron run** notices when the public site changes, even when the code does not.
- **`workflow_dispatch`** can run the demo markers, to show failures in CI.

## Not chosen

| Option | Why not |
|---|---|
| Logging in through the form in every UI test | slow, and repeats one test hundreds of times |
| Shared test users | tests would depend on each other and could not run in parallel |
| `time.sleep` / custom wait loops | `expect` and auto-waiting locators already wait for the right condition |
| CSS or XPath locators | `data-testid` is stable and made for tests |
| Allure | pytest-html gives one self-contained file with no extra tool to install; the traces already give step-by-step detail |
| Assertions inside the client or the page objects | negative tests would need other helpers, and a failure would point at framework code instead of the test |
