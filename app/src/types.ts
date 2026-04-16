export type Preset = {
  id: string;
  name: string;
  hotkey: string;
  text: string;
  placeholders: Placeholder[];
};

export type Placeholder = {
  id: string;
  key: string;
  label: string;
};
