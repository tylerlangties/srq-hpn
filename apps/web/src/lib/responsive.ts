export const SHARED_RESPONSIVE = {
  desktopNav: "hidden md:flex",
  mobileOnly: "md:hidden",
  desktopOnlyBlock: "hidden md:block",
  containerInset: "px-4 md:px-6",
  buttonGroup: "flex flex-col gap-3 md:flex-row md:flex-wrap md:items-center",
  buttonWidth: "w-full md:w-auto",
  buttonPadding: "px-6 py-3 md:px-7 md:py-3.5",
  gridTwoThenThree: "grid gap-4 md:grid-cols-2 lg:grid-cols-3",
  gridTwoThenFour: "grid gap-4 md:grid-cols-2 lg:grid-cols-4",
  sectionHeaderWrap: "mb-6 flex flex-col items-start gap-3 md:flex-row md:items-center md:justify-between",
  sectionHeaderAction: "w-full md:w-auto md:shrink-0",
} as const;
