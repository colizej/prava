# 🚀 MVP QUICK START GUIDE
## Запуск приложения за 2-3 месяца

---

## 📋 ЧТО МЫ СТРОИМ (MVP)

### Минимальный жизнеспособный продукт включает:

```
✅ Landing page с регистрацией
✅ 15 бесплатных уроков + 39 Premium
✅ 54 экзаменационных вопроса
✅ Базовый тестовый режим
✅ Простой дашборд пользователя
✅ Интеграция платежей (Stripe)
✅ Базовая статистика прогресса

❌ НЕТ в MVP:
   - Мобильное приложение
   - AI тренер
   - Gamification
   - Темная тема
   - Offline режим
```

---

## 🛠️ ШАГИ РАЗРАБОТКИ

### ШАГ 1: Подготовка данных (1 неделя)

#### 1.1 Структурировать уроки

```bash
cd /Users/colizej/Documents/webApp/permis-conduire

# Создать директорию для структурированных данных
mkdir -p data/structured
```

```javascript
// scripts/structure-lessons.js
const fs = require('fs');
const lessonsRaw = require('../sites/readytoroad.be/output/lessons_data_complete.json');

const structuredLessons = lessonsRaw.map((lesson, index) => ({
  id: index + 1,
  title: lesson.title,
  titleNl: null, // TODO: перевод
  slug: lesson.title.toLowerCase().replace(/\s+/g, '-'),
  content: lesson.content,
  contentNl: null,
  category: lesson.category,
  orderIndex: index,
  isFree: index < 15, // Первые 15 бесплатные
  duration: Math.ceil(lesson.content.length / 200), // Примерно
  images: lesson.images || [],
}));

fs.writeFileSync(
  'data/structured/lessons.json',
  JSON.stringify(structuredLessons, null, 2)
);

console.log(`✅ Структурировано ${structuredLessons.length} уроков`);
```

#### 1.2 Структурировать вопросы

```javascript
// scripts/structure-questions.js
const fs = require('fs');
const questionsRaw = require('../sites/permisdeconduire-online.be/output/exam_questions_complete.json');

const structuredQuestions = questionsRaw.questions.map((q, index) => ({
  id: index + 1,
  questionText: q.question,
  questionTextNl: null,
  questionImageUrl: q.image || null,
  type: q.type === 'yes_no' ? 'TRUE_FALSE' : 'MULTIPLE_CHOICE',
  options: q.answers.map(a => ({
    text: a.text,
    isCorrect: a.correct === true,
    explanation: a.explanation || null
  })),
  optionsNl: null,
  explanation: q.explanation || null,
  explanationNl: null,
  articleReference: q.articleRef || null,
  category: q.category || 'general',
  difficulty: determineDifficulty(q), // Функция определения сложности
}));

function determineDifficulty(question) {
  // Простая логика: если есть картинка - medium, если объяснение длинное - hard
  if (question.explanation && question.explanation.length > 200) return 'HARD';
  if (question.image) return 'MEDIUM';
  return 'EASY';
}

fs.writeFileSync(
  'data/structured/questions.json',
  JSON.stringify(structuredQuestions, null, 2)
);

console.log(`✅ Структурировано ${structuredQuestions.length} вопросов`);
```

#### 1.3 Структурировать дорожные знаки

```javascript
// scripts/structure-signs.js
const fs = require('fs');
const signsRaw = require('../sites/codedelaroute.be/output/code_de_la_route_complet.json');

const structuredSigns = signsRaw.signs.map((sign, index) => ({
  id: index + 1,
  name: sign.name,
  nameNl: null,
  category: sign.category,
  imageUrl: sign.imageUrl,
  description: sign.description,
  descriptionNl: null,
  officialCode: sign.code || null,
}));

fs.writeFileSync(
  'data/structured/road-signs.json',
  JSON.stringify(structuredSigns, null, 2)
);

console.log(`✅ Структурировано ${structuredSigns.length} знаков`);
```

#### Запуск скриптов:

```bash
node scripts/structure-lessons.js
node scripts/structure-questions.js
node scripts/structure-signs.js
```

---

### ШАГ 2: Инициализация проекта (2-3 дня)

#### 2.1 Создать Next.js проект

```bash
# Создать новую директорию для MVP
cd /Users/colizej/Documents/webApp
npx create-next-app@latest permis-ready --typescript --tailwind --app --eslint

cd permis-ready
```

#### 2.2 Установить зависимости

```bash
# UI компоненты
npm install @shadcn/ui lucide-react framer-motion

# Формы и валидация
npm install react-hook-form zod @hookform/resolvers

# База данных
npm install @prisma/client
npm install -D prisma

# Аутентификация
npm install @clerk/nextjs

# Платежи
npm install stripe @stripe/stripe-js

# State management
npm install zustand

# Утилиты
npm install date-fns clsx tailwind-merge

# Графики
npm install recharts
```

#### 2.3 Инициализировать Prisma

```bash
npx prisma init
```

Скопировать схему из `TECHNICAL_ARCHITECTURE.md` в `prisma/schema.prisma`

```bash
# Создать миграцию
npx prisma migrate dev --name init

# Сгенерировать клиент
npx prisma generate
```

---

### ШАГ 3: Импорт данных в БД (1 день)

#### 3.1 Скрипт для импорта

```typescript
// scripts/seed-database.ts
import { PrismaClient } from '@prisma/client';
import lessonsData from '../data/structured/lessons.json';
import questionsData from '../data/structured/questions.json';
import signsData from '../data/structured/road-signs.json';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Начинаем заполнение базы данных...');

  // Импорт уроков
  console.log('📚 Импорт уроков...');
  for (const lesson of lessonsData) {
    await prisma.lesson.create({
      data: lesson
    });
  }
  console.log(`✅ Импортировано ${lessonsData.length} уроков`);

  // Импорт вопросов
  console.log('❓ Импорт вопросов...');
  for (const question of questionsData) {
    await prisma.question.create({
      data: question
    });
  }
  console.log(`✅ Импортировано ${questionsData.length} вопросов`);

  // Импорт знаков
  console.log('🚦 Импорт дорожных знаков...');
  for (const sign of signsData) {
    await prisma.roadSign.create({
      data: sign
    });
  }
  console.log(`✅ Импортировано ${signsData.length} знаков`);

  console.log('🎉 База данных заполнена!');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
```

```bash
# Добавить в package.json
"scripts": {
  "db:seed": "tsx scripts/seed-database.ts"
}

# Установить tsx
npm install -D tsx

# Запустить
npm run db:seed
```

---

### ШАГ 4: Настройка аутентификации (1 день)

#### 4.1 Настроить Clerk

1. Зарегистрироваться на [clerk.com](https://clerk.com)
2. Создать приложение
3. Получить API ключи

```bash
# .env.local
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

#### 4.2 Настроить middleware

```typescript
// middleware.ts
import { authMiddleware } from "@clerk/nextjs";

export default authMiddleware({
  publicRoutes: [
    "/",
    "/sign-in(.*)",
    "/sign-up(.*)",
    "/api/webhook(.*)",
    "/lessons", // Можно смотреть список
    "/pricing"
  ],
});

export const config = {
  matcher: ["/((?!.+\\.[\\w]+$|_next).*)", "/", "/(api|trpc)(.*)"],
};
```

---

### ШАГ 5: Создать основные API endpoints (1 неделя)

#### 5.1 Lessons API

```typescript
// app/api/lessons/route.ts
import { prisma } from '@/lib/prisma';
import { auth } from '@clerk/nextjs';
import { NextResponse } from 'next/server';

export async function GET() {
  const { userId } = auth();

  const lessons = await prisma.lesson.findMany({
    where: userId ? undefined : { isFree: true }, // Показываем все если залогинен
    orderBy: { orderIndex: 'asc' },
    select: {
      id: true,
      title: true,
      slug: true,
      category: true,
      orderIndex: true,
      isFree: true,
      duration: true,
      // content показываем только Premium пользователям
      content: userId ? true : false,
    }
  });

  return NextResponse.json(lessons);
}
```

```typescript
// app/api/lessons/[id]/route.ts
import { prisma } from '@/lib/prisma';
import { auth } from '@clerk/nextjs';
import { NextResponse } from 'next/server';

export async function GET(
  req: Request,
  { params }: { params: { id: string } }
) {
  const { userId } = auth();
  const lessonId = parseInt(params.id);

  const lesson = await prisma.lesson.findUnique({
    where: { id: lessonId }
  });

  if (!lesson) {
    return NextResponse.json(
      { error: 'Lesson not found' },
      { status: 404 }
    );
  }

  // Проверка доступа
  if (!lesson.isFree && !userId) {
    return NextResponse.json(
      { error: 'Premium content. Please sign in.' },
      { status: 403 }
    );
  }

  // Проверка подписки
  if (!lesson.isFree && userId) {
    const user = await prisma.user.findUnique({
      where: { clerkId: userId }
    });

    if (user?.subscriptionTier === 'FREE') {
      return NextResponse.json(
        { error: 'Premium content. Please upgrade.' },
        { status: 403 }
      );
    }
  }

  return NextResponse.json(lesson);
}
```

#### 5.2 Questions API

```typescript
// app/api/questions/random/route.ts
import { prisma } from '@/lib/prisma';
import { auth } from '@clerk/nextjs';
import { NextResponse } from 'next/server';

export async function GET(req: Request) {
  const { userId } = auth();
  const { searchParams } = new URL(req.url);

  const count = parseInt(searchParams.get('count') || '10');
  const category = searchParams.get('category');

  // Free users - only 10 questions per day
  if (!userId) {
    return NextResponse.json(
      { error: 'Please sign in for practice tests' },
      { status: 401 }
    );
  }

  const user = await prisma.user.findUnique({
    where: { clerkId: userId }
  });

  // Check daily limit for free users
  if (user?.subscriptionTier === 'FREE') {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const todayAttempts = await prisma.testAttempt.count({
      where: {
        userId: user.id,
        startedAt: { gte: today }
      }
    });

    if (todayAttempts >= 1) { // 1 test per day for free
      return NextResponse.json(
        { error: 'Daily limit reached. Upgrade to Premium for unlimited tests.' },
        { status: 429 }
      );
    }
  }

  // Get random questions
  const where = category ? { category } : {};

  const questions = await prisma.$queryRaw`
    SELECT * FROM "Question"
    ${category ? `WHERE category = ${category}` : ''}
    ORDER BY RANDOM()
    LIMIT ${count}
  `;

  return NextResponse.json(questions);
}
```

#### 5.3 Tests API

```typescript
// app/api/tests/submit/route.ts
import { prisma } from '@/lib/prisma';
import { auth } from '@clerk/nextjs';
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const { userId } = auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await req.json();
  const { testType, questions, answers, startedAt } = body;

  const user = await prisma.user.findUnique({
    where: { clerkId: userId }
  });

  if (!user) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }

  // Calculate score
  let score = 0;
  const detailedResults = questions.map((q: any, index: number) => {
    const userAnswer = answers[index];
    const correctOption = q.options.find((o: any) => o.isCorrect);
    const isCorrect = userAnswer === correctOption?.text;

    if (isCorrect) score++;

    return {
      questionId: q.id,
      userAnswer,
      correctAnswer: correctOption?.text,
      isCorrect,
      explanation: q.explanation
    };
  });

  const percentage = (score / questions.length) * 100;
  const passed = percentage >= 82; // 41/50 for exam

  // Save test attempt
  const testAttempt = await prisma.testAttempt.create({
    data: {
      userId: user.id,
      testType,
      questions: detailedResults,
      score,
      totalQuestions: questions.length,
      percentage,
      passed,
      startedAt: new Date(startedAt),
      finishedAt: new Date(),
      timeTaken: Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000)
    }
  });

  // Update user stats
  await updateUserStats(user.id, score, questions.length);

  return NextResponse.json({
    testId: testAttempt.id,
    score,
    totalQuestions: questions.length,
    percentage,
    passed,
    results: detailedResults
  });
}

async function updateUserStats(userId: string, score: number, total: number) {
  const xpGained = score * 10; // 10 XP per correct answer

  await prisma.userStats.upsert({
    where: { userId },
    update: {
      totalXp: { increment: xpGained },
      level: { increment: Math.floor(xpGained / 100) } // Level up every 100 XP
    },
    create: {
      userId,
      totalXp: xpGained,
      level: 1
    }
  });
}
```

---

### ШАГ 6: Создать Frontend страницы (2 недели)

#### 6.1 Landing Page

```typescript
// app/page.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h1 className="text-5xl font-bold mb-6">
          Réussissez votre permis de conduire
          <span className="text-blue-600"> du premier coup</span>
        </h1>

        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Préparez-vous efficacement avec 54 leçons complètes,
          des centaines de questions et un suivi personnalisé.
        </p>

        <div className="flex gap-4 justify-center">
          <Button size="lg" asChild>
            <Link href="/sign-up">Commencer gratuitement</Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/pricing">Voir les prix</Link>
          </Button>
        </div>

        <div className="mt-12 grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="p-6 bg-white rounded-lg shadow">
            <div className="text-4xl mb-4">📚</div>
            <h3 className="font-bold mb-2">54 Leçons</h3>
            <p className="text-gray-600">Cours complets et structurés</p>
          </div>

          <div className="p-6 bg-white rounded-lg shadow">
            <div className="text-4xl mb-4">❓</div>
            <h3 className="font-bold mb-2">250+ Questions</h3>
            <p className="text-gray-600">Entraînement illimité</p>
          </div>

          <div className="p-6 bg-white rounded-lg shadow">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="font-bold mb-2">Suivi détaillé</h3>
            <p className="text-gray-600">Analysez votre progression</p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">
            Tout ce dont vous avez besoin
          </h2>

          {/* Feature list */}
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <Feature
              icon="✅"
              title="Contenu officiel"
              description="Basé sur le code de la route belge"
            />
            <Feature
              icon="🎯"
              title="Tests réalistes"
              description="Simulations d'examen authentiques"
            />
            <Feature
              icon="📱"
              title="Accessible partout"
              description="Web, iOS et Android"
            />
            <Feature
              icon="💰"
              title="Prix abordable"
              description="À partir de €9.99/mois"
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h2 className="text-3xl font-bold mb-6">
          Prêt à commencer ?
        </h2>
        <p className="text-xl text-gray-600 mb-8">
          Rejoignez des milliers d'étudiants qui ont réussi leur permis
        </p>
        <Button size="lg" asChild>
          <Link href="/sign-up">Commencer gratuitement</Link>
        </Button>
      </section>
    </main>
  );
}

function Feature({ icon, title, description }: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="text-3xl">{icon}</div>
      <div>
        <h3 className="font-bold mb-1">{title}</h3>
        <p className="text-gray-600">{description}</p>
      </div>
    </div>
  );
}
```

#### 6.2 Lessons Page

```typescript
// app/lessons/page.tsx
import { prisma } from '@/lib/prisma';
import { auth } from '@clerk/nextjs';
import LessonCard from '@/components/LessonCard';

export default async function LessonsPage() {
  const { userId } = auth();

  const lessons = await prisma.lesson.findMany({
    orderBy: { orderIndex: 'asc' },
  });

  const user = userId ? await prisma.user.findUnique({
    where: { clerkId: userId },
    include: { progress: true }
  }) : null;

  const groupedLessons = lessons.reduce((acc, lesson) => {
    if (!acc[lesson.category]) {
      acc[lesson.category] = [];
    }
    acc[lesson.category].push(lesson);
    return acc;
  }, {} as Record<string, typeof lessons>);

  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-4xl font-bold mb-8">Cours théoriques</h1>

      {Object.entries(groupedLessons).map(([category, categoryLessons]) => (
        <div key={category} className="mb-12">
          <h2 className="text-2xl font-bold mb-4 capitalize">{category}</h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categoryLessons.map(lesson => {
              const progress = user?.progress.find(p => p.lessonId === lesson.id);
              const hasAccess = lesson.isFree || user?.subscriptionTier !== 'FREE';

              return (
                <LessonCard
                  key={lesson.id}
                  lesson={lesson}
                  completed={progress?.completed || false}
                  hasAccess={hasAccess}
                />
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
```

```typescript
// components/LessonCard.tsx
'use client';

import Link from 'next/link';
import { Lock, Check, Clock } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface LessonCardProps {
  lesson: {
    id: number;
    title: string;
    slug: string;
    duration: number | null;
    isFree: boolean;
  };
  completed: boolean;
  hasAccess: boolean;
}

export default function LessonCard({ lesson, completed, hasAccess }: LessonCardProps) {
  return (
    <Link href={hasAccess ? `/lessons/${lesson.slug}` : '/pricing'}>
      <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer relative">
        {!hasAccess && (
          <div className="absolute top-4 right-4">
            <Lock className="w-5 h-5 text-gray-400" />
          </div>
        )}

        {completed && (
          <div className="absolute top-4 right-4">
            <Check className="w-5 h-5 text-green-500" />
          </div>
        )}

        <h3 className="font-bold mb-2">{lesson.title}</h3>

        {lesson.duration && (
          <div className="flex items-center text-sm text-gray-600">
            <Clock className="w-4 h-4 mr-1" />
            {lesson.duration} min
          </div>
        )}

        {!lesson.isFree && (
          <div className="mt-4">
            <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">
              Premium
            </span>
          </div>
        )}
      </Card>
    </Link>
  );
}
```

#### 6.3 Practice Test Page

```typescript
// app/practice/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import QuizEngine from '@/components/QuizEngine';
import { Button } from '@/components/ui/button';

export default function PracticePage() {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchQuestions();
  }, []);

  async function fetchQuestions() {
    try {
      const response = await fetch('/api/questions/random?count=20');

      if (!response.ok) {
        const error = await response.json();
        alert(error.error);
        router.push('/pricing');
        return;
      }

      const data = await response.json();
      setQuestions(data);
    } catch (error) {
      console.error('Error fetching questions:', error);
    } finally {
      setLoading(false);
    }
  }

  function handleTestComplete(results: any) {
    router.push(`/results/${results.testId}`);
  }

  if (loading) {
    return <div className="container mx-auto px-4 py-12">Chargement...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <QuizEngine
        questions={questions}
        mode="practice"
        onComplete={handleTestComplete}
      />
    </div>
  );
}
```

---

### ШАГ 7: Интеграция платежей Stripe (3-4 дня)

#### 7.1 Настройка Stripe

```bash
# .env.local
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Pricing IDs из Stripe Dashboard
PRICE_BASIC_MONTHLY=price_...
PRICE_PREMIUM_3MONTH=price_...
PRICE_SUPER_YEARLY=price_...
```

#### 7.2 Checkout API

```typescript
// app/api/subscriptions/checkout/route.ts
import { auth } from '@clerk/nextjs';
import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { prisma } from '@/lib/prisma';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

export async function POST(req: Request) {
  const { userId } = auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { priceId, tier } = await req.json();

  const user = await prisma.user.findUnique({
    where: { clerkId: userId }
  });

  if (!user) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }

  // Create checkout session
  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    payment_method_types: ['card'],
    line_items: [
      {
        price: priceId,
        quantity: 1,
      },
    ],
    success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?success=true`,
    cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing?canceled=true`,
    metadata: {
      userId: user.id,
      tier,
    },
    customer_email: user.email,
  });

  return NextResponse.json({ url: session.url });
}
```

#### 7.3 Stripe Webhook

```typescript
// app/api/webhooks/stripe/route.ts
import { headers } from 'next/headers';
import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { prisma } from '@/lib/prisma';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

export async function POST(req: Request) {
  const body = await req.text();
  const signature = headers().get('stripe-signature')!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    );
  }

  // Handle events
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutCompleted(session);
      break;
    }

    case 'customer.subscription.updated': {
      const subscription = event.data.object as Stripe.Subscription;
      await handleSubscriptionUpdated(subscription);
      break;
    }

    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;
      await handleSubscriptionCanceled(subscription);
      break;
    }
  }

  return NextResponse.json({ received: true });
}

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  const userId = session.metadata?.userId;
  const tier = session.metadata?.tier as any;

  if (!userId || !tier) return;

  // Calculate expiry date based on tier
  const expiresAt = new Date();
  if (tier === 'BASIC') {
    expiresAt.setMonth(expiresAt.getMonth() + 1);
  } else if (tier === 'PREMIUM') {
    expiresAt.setMonth(expiresAt.getMonth() + 3);
  } else if (tier === 'SUPER_PREMIUM') {
    expiresAt.setFullYear(expiresAt.getFullYear() + 1);
  }

  // Update user subscription
  await prisma.user.update({
    where: { id: userId },
    data: {
      subscriptionTier: tier,
      subscriptionExpiresAt: expiresAt,
    },
  });

  // Create payment record
  await prisma.payment.create({
    data: {
      userId,
      amount: session.amount_total! / 100,
      currency: session.currency!.toUpperCase(),
      status: 'completed',
      paymentProvider: 'stripe',
      providerPaymentId: session.id,
      subscriptionTier: tier,
    },
  });
}

async function handleSubscriptionUpdated(subscription: Stripe.Subscription) {
  // Handle subscription renewal, etc.
}

async function handleSubscriptionCanceled(subscription: Stripe.Subscription) {
  // Downgrade user to FREE
}
```

---

### ШАГ 8: Деплой (2-3 дня)

#### 8.1 Подготовка к деплою

```bash
# Проверить production build
npm run build

# Настроить переменные окружения на Vercel
# DATABASE_URL, CLERK keys, STRIPE keys, etc.
```

#### 8.2 Deплой на Vercel

```bash
# Установить Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

#### 8.3 Настроить базу данных (Production)

Варианты:
1. **Supabase** (рекомендуется для начала) - бесплатный tier
2. **Railway** - €5/месяц
3. **Neon** - serverless PostgreSQL
4. **AWS RDS** - для масштаба

```bash
# После создания production БД
DATABASE_URL="postgresql://user:pass@host:5432/db" npm run db:migrate
DATABASE_URL="postgresql://user:pass@host:5432/db" npm run db:seed
```

---

## 📊 ЧЕКЛИСТ ЗАПУСКА MVP

### Pre-launch (за 2 недели)

```
☐ Создать Landing page с email сбором
☐ Настроить Google Analytics / Mixpanel
☐ Подготовить контент для соц. сетей
☐ Написать пресс-релиз
☐ Подготовить FAQ
☐ Настроить email автоматизацию (Resend/Mailchimp)
```

### Launch day

```
☐ Проверить все функции в production
☐ Убедиться, что платежи работают
☐ Опубликовать в соц. сетях
☐ Отправить email подписчикам
☐ Опубликовать на Product Hunt
☐ Мониторить ошибки (Sentry)
```

### Post-launch (первая неделя)

```
☐ Собрать первые 10 отзывов
☐ Исправить критические баги
☐ Начать A/B тесты ценообразования
☐ Оптимизировать conversion funnel
☐ Планировать следующие фичи
```

---

## 🎯 МЕТРИКИ УСПЕХА MVP

### Неделя 1
- ✅ 100+ регистраций
- ✅ 10+ платных пользователей
- ✅ 0 критических багов

### Месяц 1
- ✅ 500+ регистраций
- ✅ 50+ платных пользователей (conversion 10%+)
- ✅ MRR: €500+

### Месяц 3
- ✅ 2000+ регистраций
- ✅ 200+ платных пользователей
- ✅ MRR: €3,000+
- ✅ Retention Day 7: 40%+

---

## 💡 СОВЕТЫ ПО ОПТИМИЗАЦИИ

### Performance

```typescript
// 1. Image optimization
import Image from 'next/image';

<Image
  src="/signs/stop.png"
  alt="Stop sign"
  width={200}
  height={200}
  loading="lazy"
/>

// 2. Code splitting
const QuizEngine = dynamic(() => import('@/components/QuizEngine'), {
  loading: () => <p>Loading quiz...</p>,
  ssr: false
});

// 3. Cache API responses
export async function GET() {
  const lessons = await prisma.lesson.findMany();

  return NextResponse.json(lessons, {
    headers: {
      'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400'
    }
  });
}
```

### SEO

```typescript
// app/layout.tsx
export const metadata = {
  title: 'PermisReady - Préparation examen permis de conduire Belgique',
  description: '54 leçons, 250+ questions. Réussissez votre permis du premier coup.',
  keywords: ['permis de conduire', 'belgique', 'examen théorique', 'code de la route'],
  openGraph: {
    title: 'PermisReady - Réussissez votre permis',
    description: 'Préparation complète à l\'examen théorique',
    images: ['/og-image.png'],
  },
};
```

### Conversion Optimization

```typescript
// A/B testing prix (example with Vercel's Edge Config)

export default function PricingPage() {
  const variant = useABTest('pricing_test');

  const basicPrice = variant === 'A' ? 9.99 : 12.99;

  return (
    <PricingCard tier="basic" price={basicPrice} />
  );
}
```

---

## 🚀 ГОТОВО!

Следуя этому гайду, вы создадите работающий MVP за **2-3 месяца**.

### Следующие шаги после MVP:

1. ✅ Собрать feedback от первых 100 пользователей
2. ✅ Итерировать на основе данных
3. ✅ Добавить мобильное приложение
4. ✅ Внедрить AI тренера
5. ✅ Масштабироваться!

**Удачи! 🎉**
