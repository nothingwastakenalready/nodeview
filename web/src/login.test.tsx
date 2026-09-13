import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, test } from "vitest";

import { LoginPage } from "./LoginPage";

describe("LoginPage", () => {
  test("offers registration only once and keeps secondary actions grouped", () => {
    const html = renderToStaticMarkup(<LoginPage onAuthenticated={() => undefined} />);

    expect(html.match(/href="#\/register"/g)).toHaveLength(1);
    expect(html).toContain("login-secondary-actions");
    expect(html).toContain("forgot password?");
    expect(html).toContain("Create a new account");
  });
});
