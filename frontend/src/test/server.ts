import { setupServer } from "msw/node";
import { handlers } from "./handlers/api";

export const server = setupServer(...handlers);
