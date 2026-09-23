export function isChatgptUrl(value) {
  if (typeof value !== "string") return false;
  try {
    return new URL(value).origin === "https://chatgpt.com";
  } catch (error) {
    return false;
  }
}

export function isProjectPath(value) {
  if (typeof value !== "string") return false;
  try {
    const parsed = new URL(value);
    if (parsed.origin !== "https://chatgpt.com") return false;
    const segments = parsed.pathname.split("/").filter(Boolean);
    return segments.some(
      (segment, index) =>
        segment === "g" &&
        index + 1 < segments.length &&
        segments[index + 1].startsWith("g-p-")
    );
  } catch (error) {
    return false;
  }
}
