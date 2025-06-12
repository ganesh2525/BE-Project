# Use a specific Node version (for stability)
FROM node:18

# Set working directory
WORKDIR /app/backend

# Copy only package.json and package-lock.json first for caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Now copy the rest of the app
COPY . .

# Set environment variables
ENV DB_user=value \
    DB_password=value \
    DB_name=value \
    SECRET_KEY=value \
    EMAIL=value \
    PASSWORD=value

# Start the server
CMD ["node", "server.js"]
