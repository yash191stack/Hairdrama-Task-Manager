CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar TEXT,
    google_id VARCHAR(255) UNIQUE,
    github_id VARCHAR(255) UNIQUE,
    role VARCHAR(20) CHECK (role IN ('admin', 'user')) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(30) CHECK (status IN ('pending', 'assigned', 'in_progress', 'submitted', 'accepted', 'revision_requested')) DEFAULT 'pending',
    product_image_url TEXT,
    created_by UUID REFERENCES users(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generated_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    image_type VARCHAR(50) CHECK (image_type IN ('white_background', 'theme', 'creative', 'model')) NOT NULL,
    image_url TEXT NOT NULL,
    prompt_used TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    angle VARCHAR(20) CHECK (angle IN ('front', 'side', 'close_up', 'none')) DEFAULT 'none',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    row_id VARCHAR(255) NOT NULL,
    changes JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_select_policy ON users
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY users_update_policy ON users
    FOR UPDATE TO authenticated
    USING (auth.uid() = id OR EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    ));

CREATE POLICY tasks_select_policy ON tasks
    FOR SELECT TO authenticated
    USING (
        created_by = auth.uid() OR 
        assigned_to = auth.uid() OR 
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY tasks_write_policy ON tasks
    FOR ALL TO authenticated
    USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    )
    WITH CHECK (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY tasks_user_update_status ON tasks
    FOR UPDATE TO authenticated
    USING (assigned_to = auth.uid())
    WITH CHECK (assigned_to = auth.uid());

CREATE POLICY images_select_policy ON generated_images
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM tasks 
            WHERE tasks.id = task_id AND (
                tasks.created_by = auth.uid() OR 
                tasks.assigned_to = auth.uid() OR
                EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
            )
        )
    );

CREATE POLICY images_write_policy ON generated_images
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM tasks 
            WHERE tasks.id = task_id AND (
                tasks.assigned_to = auth.uid() OR
                EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
            )
        )
    );

CREATE POLICY audit_logs_select_policy ON audit_logs
    FOR SELECT TO authenticated
    USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );
