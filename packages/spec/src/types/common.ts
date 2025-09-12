export type ULID = string & { readonly __brand: "ULID" };
export type ISODateString = string & { readonly __brand: "ISODate" };

export type Metadata = {
  id: ULID;
  name: string; // kebab-case
  description?: string;
  version: string; // semantic
  createdAt: ISODateString;
  updatedAt: ISODateString;
  tags?: string[];
};
