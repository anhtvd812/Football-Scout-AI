import { isUsingMock } from '../../api/client'

export function Header() {
  return (
    <header className="border-b border-white/10 bg-black/20 backdrop-blur-md sticky top-0 z-30">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-xl">
            ⚽
          </span>
          <div>
            <h1 className="text-lg font-bold text-white sm:text-xl">Football Scout AI</h1>
            <p className="text-xs text-slate-400">Khám phá & Định giá cầu thủ</p>
          </div>
        </div>
        {isUsingMock() && (
          <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[10px] font-medium text-amber-300">
            Demo · Mock data
          </span>
        )}
      </div>
    </header>
  )
}
