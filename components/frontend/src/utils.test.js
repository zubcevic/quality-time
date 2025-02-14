import { renderHook, act } from '@testing-library/react-hooks'
import { createMemoryHistory } from 'history';
import {
    capitalize, getUserPermissions, get_metric_tags, get_metric_target, get_source_name, get_subject_name,
    nice_number, scaled_number, registeredURLSearchParams, userPrefersDarkMode, useURLSearchQuery, getMetricResponseOverrun
} from './utils';
import { EDIT_REPORT_PERMISSION, EDIT_ENTITY_PERMISSION } from './context/Permissions';

it('capitalizes strings', () => {
    expect(capitalize("")).toBe("")
    expect(capitalize("A")).toBe("A")
    expect(capitalize("a")).toBe("A")
    expect(capitalize("ab")).toBe("Ab")
    expect(capitalize("aB")).toBe("AB")
    expect(capitalize("AB")).toBe("AB")
});

it('rounds numbers nicely', () => {
    expect(nice_number(15)).toBe(20);
    expect(nice_number(16)).toBe(20);
    expect(nice_number(17)).toBe(50);
    expect(nice_number(39)).toBe(50);
    expect(nice_number(40)).toBe(50);
    expect(nice_number(41)).toBe(100);
    expect(nice_number(79)).toBe(100);
    expect(nice_number(80)).toBe(100);
    expect(nice_number(81)).toBe(200);
});

it('adds a scale', () => {
    expect(scaled_number(1)).toBe("1");
    expect(scaled_number(12)).toBe("12");
    expect(scaled_number(123)).toBe("123");
    expect(scaled_number(1234)).toBe("1k");
    expect(scaled_number(12345)).toBe("12k");
    expect(scaled_number(123456)).toBe("123k");
    expect(scaled_number(1234567)).toBe("1m");
    expect(scaled_number(12345678)).toBe("12m");
    expect(scaled_number(123456789)).toBe("123m");
});

it('gives users all permissions if permissions have not been limited', () => {
    const permissions = getUserPermissions("jodoe", "john.doe@example.org", false, null, {});
    expect(permissions).toStrictEqual([EDIT_REPORT_PERMISSION, EDIT_ENTITY_PERMISSION]);
});

it('gives users edit report permissions if edit report permissions have been granted', () => {
    const permissions = getUserPermissions("jodoe", "john.doe@example.org", false, null, { [EDIT_REPORT_PERMISSION]: ["jodoe"], [EDIT_ENTITY_PERMISSION]: ["jadoe"] });
    expect(permissions).toStrictEqual([EDIT_REPORT_PERMISSION]);
});

it('gives users edit entity permissions if edit entity permissions have been granted', () => {
    const permissions = getUserPermissions("jodoe", "john.doe@example.org", false, null, { [EDIT_REPORT_PERMISSION]: ["jadoe"], [EDIT_ENTITY_PERMISSION]: ["jodoe"] });
    expect(permissions).toStrictEqual([EDIT_ENTITY_PERMISSION]);
});

it('gives users no permissions if they have not logged in', () => {
    const permissions = getUserPermissions(null, null, false, null, {});
    expect(permissions).toStrictEqual([]);
});

it('gives users no permissions if the report date is in the past', () => {
    const permissions = getUserPermissions("jodoe", "john.doe@example.org", false, new Date(), {});
    expect(permissions).toStrictEqual([]);
});

it('gives users no permissions if the report is a tag report', () => {
    const permissions = getUserPermissions("jodoe", "john.doe@example.org", true, null, {});
    expect(permissions).toStrictEqual([]);
});

it('gets the metric tags sorted', () => {
    expect(get_metric_tags({ tags: ["foo", "bar"] })).toStrictEqual(["bar", "foo"]);
});

it('gets the metric tags even if there are none', () => {
    expect(get_metric_tags({})).toStrictEqual([]);
});

it('gets the metric target', () => {
    expect(get_metric_target({ target: "2" })).toStrictEqual("2");
});

it('gets the metric target, even if the target is missing', () => {
    expect(get_metric_target({})).toStrictEqual("0");
});

it('gets the source name', () => {
    expect(get_source_name({ name: "source" }, {})).toStrictEqual("source")
});

it('gets the source name from the data model if the source has no name', () => {
    expect(get_source_name({ type: "source_type" }, { sources: { "source_type": { name: "source" } } })).toStrictEqual("source")
});

it('gets the subject name', () => {
    expect(get_subject_name({ name: "subject" }, {})).toStrictEqual("subject")
});

it('gets the subject name from the data model if the subject has no name', () => {
    expect(get_subject_name({ type: "subject_type" }, { subjects: { "subject_type": { name: "subject" } } })).toStrictEqual("subject")
});

it('gets a boolean value', () => {
    const history = createMemoryHistory({ initialEntries: ['?key=true'] })
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "boolean"))
    expect(result.current[0]).toBe(true)
})

it('gets the default boolean value', () => {
    const history = createMemoryHistory()
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "boolean", false))
    expect(result.current[0]).toBe(false)
})

it('sets a boolean value', () => {
    const history = createMemoryHistory()
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "boolean", false))
    act(() => { result.current[1](true) })
    expect(result.current[0]).toBe(true)
    expect(history.location.search).toEqual("?key=true")
})

it('removes the boolean value when set to default value', () => {
    const history = createMemoryHistory()
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "boolean", false))
    act(() => { result.current[1](true) })
    act(() => { result.current[1](false) })
    expect(result.current[0]).toBe(false)
    expect(history.location.search).toEqual("")
})

it('gets an integer value', () => {
    const history = createMemoryHistory({ initialEntries: ['?key=42'] })
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "integer"))
    expect(result.current[0]).toBe(42)
})

it('gets the default integer value', () => {
    const history = createMemoryHistory()
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "integer", 7))
    expect(result.current[0]).toBe(7)
})

it('sets an integer value', () => {
    const history = createMemoryHistory()
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "integer", 0))
    act(() => { result.current[1](42) })
    expect(result.current[0]).toBe(42)
    expect(history.location.search).toEqual("?key=42")
})

it('removes the integer value when set to the default value', () => {
    const history = createMemoryHistory({ initialEntries: ['?key=42'] })
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "integer", 2))
    act(() => { result.current[1](2) })
    expect(history.location.search).toEqual("")
})

it('gets an array value', () => {
    const history = createMemoryHistory({ initialEntries: ['?key=a,b'] })
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "array"))
    expect(result.current[0]).toStrictEqual(["a", "b"])
})

it('sets an array value', () => {
    const history = createMemoryHistory()
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "array"))
    act(() => { result.current[1]("a") })
    act(() => { result.current[1]("b") })
    expect(result.current[0]).toStrictEqual(["a", "b"])
    expect(history.location.search).toEqual("?key=a,b")
})

it('unsets an array value', () => {
    const history = createMemoryHistory({ initialEntries: ['?key=a'] })
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "array"))
    act(() => { result.current[1]("a") })
    expect(result.current[0]).toStrictEqual([])
    expect(history.location.search).toEqual("")
})

it('clears the array value', () => {
    const history = createMemoryHistory()
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "array"))
    act(() => { result.current[1]("a") })
    act(() => { result.current[1]("b") })
    act(() => { result.current[2]() })
    expect(result.current[0]).toStrictEqual([])
    expect(history.location.search).toEqual("")
})

it('sets both a boolean and an integer parameter', () => {
    const history = createMemoryHistory()
    const hook1 = renderHook(() => useURLSearchQuery(history, "boolean_key", "boolean"))
    act(() => { hook1.result.current[1](true) })
    const hook2 = renderHook(() => useURLSearchQuery(history, "integer_key", "integer"))
    act(() => { hook2.result.current[1](42) })
    expect(history.location.search).toEqual("?boolean_key=true&integer_key=42")
})

it('gets a string value', () => {
    const history = createMemoryHistory({ initialEntries: ['?key=value'] })
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "string"))
    expect(result.current[0]).toBe("value")
})

it('gets the default string value', () => {
    const history = createMemoryHistory()
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "string", "default"))
    expect(result.current[0]).toBe("default")
})

it('sets a string value', () => {
    const history = createMemoryHistory()
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "string", ""))
    act(() => { result.current[1]("value") })
    expect(result.current[0]).toBe("value")
    expect(history.location.search).toEqual("?key=value")
})

it('removes the string value when set to the default value', () => {
    const history = createMemoryHistory({ initialEntries: ['?key=value'] })
    const { result } = renderHook(() => useURLSearchQuery(history, "key", "string", "default"))
    act(() => { result.current[1]("default") })
    expect(history.location.search).toEqual("")
})

it('returns registered URL search parameters only', () => {
    const history = createMemoryHistory({ initialEntries: ['?unregistered_key=value&report_date=2022-02-11'] })
    const expected = new URLSearchParams("?report_date=2022-02-11")
    expect(registeredURLSearchParams(history).toString()).toEqual(expected.toString())
})

it("returns true when the user sets dark mode", () => {
    expect(userPrefersDarkMode("dark")).toBe(true)
})

it("returns false when the user sets light mode", () => {
    expect(userPrefersDarkMode("light")).toBe(false)
})

let matchMediaMatches

beforeAll(() => {
    Object.defineProperty(window, 'matchMedia', {
        value: jest.fn().mockImplementation(_query => ({
            matches: matchMediaMatches,
        })),
    });
});

it("returns true when the user prefers dark mode", () => {
    matchMediaMatches = true
    expect(userPrefersDarkMode(null)).toBe(true)
})

it("returns false when the user prefers light mode", () => {
    matchMediaMatches = false
    expect(userPrefersDarkMode(null)).toBe(false)
})

it("returns the metric response overrun when there are no measurements", () => {
    expect(getMetricResponseOverrun("uuid", {}, {}, [])).toStrictEqual({"overruns": [], "totalOverrun": 0})
})

it("returns the metric response overrun when there is no overrun", () => {
    expect(getMetricResponseOverrun("uuid", {}, {}, [{metric_uuid: "uuid", start: "2000-01-01", end: "2000-01-04"}])).toStrictEqual(
        {"overruns": [], "totalOverrun": 0}
    )
})

it("returns the metric response overrun when there is one long measurement", () => {
    expect(getMetricResponseOverrun("uuid", {}, {}, [{metric_uuid: "uuid", start: "2000-01-01", end: "2000-01-31"}])).toStrictEqual(
        {
            "overruns": [
                {
                    "status": "unknown",
                    "start": "2000-01-01",
                    "end": "2000-01-31",
                    "actual_response_time": 30,
                    "desired_response_time": 3,
                    "overrun": 27
                }
            ],
            "totalOverrun": 27
        }
    )
})

it("returns the metric response overrun when there are two consecutive measurements that together overrun", () => {
    const measurements = [
        {metric_uuid: "uuid", start: "2000-01-01", end: "2000-01-03"},
        {metric_uuid: "uuid", start: "2000-01-03", end: "2000-01-05"}
    ]
    expect(getMetricResponseOverrun("uuid", {}, {}, measurements)).toStrictEqual(
        {
            "overruns": [
                {
                    "status": "unknown",
                    "start": "2000-01-01",
                    "end": "2000-01-05",
                    "actual_response_time": 4,
                    "desired_response_time": 3,
                    "overrun": 1
                }
            ],
            "totalOverrun": 1
        }
    )
})

it("returns the metric response overrun when there are two measurements with different statuses", () => {
    const measurements = [
        {metric_uuid: "uuid", start: "2000-01-01", end: "2000-01-03"},
        {metric_uuid: "uuid", start: "2000-01-03", end: "2000-01-05", count: {status: "target_met"}}
    ]
    expect(getMetricResponseOverrun("uuid", {}, {}, measurements)).toStrictEqual({"overruns": [], "totalOverrun": 0})
})
