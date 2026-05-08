// Lint fixture — intentional MODA rule violations for snapshot testing.
// DO NOT "fix" these. Updating expected output requires regenerating
// violations.expected.json — see tests/README.md.

export const ClickableDiv = () => (
  <div onClick={() => alert("hi")}>Click me</div>
);

export const Hero = () => (
  <img src="/hero.png" />
);
